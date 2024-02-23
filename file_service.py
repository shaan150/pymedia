import os
import shutil

import aiofiles as aiofiles
from fastapi import UploadFile, File, HTTPException
from starlette.responses import FileResponse, StreamingResponse
from starlette.staticfiles import StaticFiles

from classes.enum.ServiceType import ServiceType
from classes.services.FileService import FileService

service = FileService()
os.makedirs(service.file_dir, exist_ok=True)
os.makedirs(service.image_dir, exist_ok=True)
os.makedirs(service.music_dir, exist_ok=True)
app = service.app

@app.get("/")
async def root():
    return await service.fetch_service_data()

@app.put("/upload/song")
async def upload_file(song_id: str, mp3_file: UploadFile = File(...), image_file: UploadFile = File(...)):
    if song_id is None or mp3_file is None or image_file is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        os.makedirs(service.image_dir, exist_ok=True)
        os.makedirs(service.music_dir, exist_ok=True)

        # extract extension from mp3 file and image file
        mp3_extension = mp3_file.filename.split(".")[-1]
        image_extension = image_file.filename.split(".")[-1]

        mp3_name = f"{song_id}.{mp3_extension}"
        image_name = f"{song_id}.{image_extension}"

        # Construct file paths
        mp3_file_path = os.path.join(service.music_dir, mp3_name)
        image_file_path = os.path.join(service.image_dir, image_name)

        # Save MP3 file
        async with aiofiles.open(mp3_file_path, "wb") as buffer:
            content = await mp3_file.read()  # Read content
            await buffer.write(content)  # Save to disk

        # Reset file pointer if needed
        await mp3_file.seek(0)

        # Save Image file
        async with aiofiles.open(image_file_path, "wb") as buffer:
            content = await image_file.read()  # Read content
            await buffer.write(content)  # Save to disk

        # Reset file pointer if needed
        await image_file.seek(0)

    except Exception as e:
        # Log the exception or send it back in the response
        print(f"Error saving files: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving files: {e}")

@app.delete("/delete/song")
async def delete_file(song_id: str):
    if song_id is None:
        raise HTTPException(status_code=400, detail="Invalid Request")
    try:
        mp3_file_path = os.path.join(service.music_dir, f"{song_id}.mp3")
        image_file_path = os.path.join(service.image_dir, f"{song_id}.jpg")

        if os.path.exists(mp3_file_path):
            os.remove(mp3_file_path)
        if os.path.exists(image_file_path):
            os.remove(image_file_path)
    except Exception as e:
        print(f"Error deleting files: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting files: {e}")

    return {"detail": "Files deleted successfully"}

@app.put("/upload/playlist")
async def upload_playlist(playlist_id: str, image_file: UploadFile = File(...)):
    if playlist_id is None or image_file is None:
        raise HTTPException(status_code=400, detail="Invalid Request")
    try:
        os.makedirs(service.image_dir, exist_ok=True)

        playlist_file_path = os.path.join(service.image_dir, f"{playlist_id}.json")

        async with aiofiles.open(playlist_file_path, "wb") as buffer:
            content = await image_file.read()
            await buffer.write(content)
            await image_file.seek(0)
    except Exception as e:
        print(f"Error saving files: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving files: {e}")

    return {"detail": "Playlist uploaded successfully"}

@app.delete("/delete/playlist")
async def delete_playlist(playlist_id: str):
    if playlist_id is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        playlist_file_path = os.path.join(service.image_dir, f"{playlist_id}.json")

        if os.path.exists(playlist_file_path):
            os.remove(playlist_file_path)
    except Exception as e:
        print(f"Error deleting files: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting files: {e}")

    return {"detail": "Playlist deleted successfully"}

@app.get("/download/song")
async def download_file(song_id: str):
    if song_id is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    # Find file with song_id, exclude the extension and return any file with that name
    file_location = [f for f in os.listdir(service.music_dir) if f.split(".")[0] == song_id]
    if len(file_location) == 0:
        raise HTTPException(status_code=404, detail="File not found")

    file_location = os.path.join(service.music_dir, file_location[0])

    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="File not found")

    # check if md5 is the same as the one in the database
    # if not, return error
    try:
        db_service = await service.get_service_url(ServiceType.DATABASE_SERVICE)
        song = await service.service_exception_handling(
            db_service, "songs/song", "GET", params={"song_id": song_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")

    md5 = song[0].get("md5")

    if md5 is None:
        raise HTTPException(status_code=404, detail="MD5 not found")

    file_md5 = await service.calculate_md5(file_location)

    if file_md5 != md5:
        raise HTTPException(status_code=422, detail="MD5 mismatch")

    # Asynchronous generator to stream the file
    async def file_streamer(filepath):
        async with aiofiles.open(filepath, "rb") as file:
            chunk = await file.read(64 * 1024)  # Read in chunks of 64KB
            while chunk:
                yield chunk
                chunk = await file.read(64 * 1024)

    # Get the original file name to suggest as download name
    file_name = os.path.basename(file_location)

    try:
        # Create the StreamingResponse, setting the media type and content-disposition header for download
        response = StreamingResponse(file_streamer(file_location), media_type="application/octet-stream")
        response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return response


@app.get("/download/image")
async def download_image(id: str):
    if id is None:
        raise HTTPException(status_code=400, detail="Invalid Request")
    try:
        file_location = [f for f in os.listdir(service.image_dir) if f.split(".")[0] == id]

        if len(file_location) == 0:
            raise HTTPException(status_code=404, detail="File not found")

        file_location = os.path.join(service.image_dir, file_location[0])
        if not os.path.exists(file_location):
            raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FileResponse(file_location)


@app.get("/stop")
async def stop_service():
    await service.stop()
    exit(0)