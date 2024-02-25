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
    """
    Returns the service data fetched by `fetch_service_data` method.

    :return: The service data.
    """
    return await service.fetch_service_data()

@app.put("/upload/song")
async def upload_file(song_id: str, mp3_file: UploadFile = File(...), image_file: UploadFile = File(...)):
    """
    :param song_id: The ID of the song being uploaded.
    :param mp3_file: The MP3 file to be uploaded.
    :param image_file: The image file associated with the song.
    :return: None

    This method is used to upload a song file and its associated image file. It saves the files to the appropriate directories on the server.

    If any of the parameters (`song_id`, `mp3_file`, `image_file`) is `None`, it will raise a `HTTPException` with a status code of 400 indicating an invalid request.

    The method first creates the necessary directories (`service.image_dir`, `service.music_dir`) if they do not exist.

    It then extracts the file extensions from the `mp3_file` and `image_file` filenames.

    Next, it constructs file paths for the MP3 file and the image file using the `song_id` and the extracted extensions.

    The method saves the MP3 file by opening a binary file for writing and writing the contents of the `mp3_file` to the buffer. It then saves the buffer to disk.

    The file pointer for the MP3 file is then reset to the beginning, in case it needs to be read again.

    The same process is then repeated for the image file.

    If any exception occurs during the file saving process, it will be logged and a `HTTPException` with a status code of 500 will be raised.

    Note: This method uses async/await syntax for asynchronous file operations.
    """
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
    """
    Delete the MP3 and image files associated with the provided song ID.

    :param song_id: The ID of the song.
    :type song_id: str
    :return: A dictionary with the detail of the deletion process.
    :rtype: dict
    :raises HTTPException: If the song ID is invalid or an error occurs while deleting the files.
    """
    if song_id is None or song_id == "":
        raise HTTPException(status_code=400, detail="Invalid Request")
    try:
        mp3_file_path = os.path.join(service.music_dir, f"{song_id}.mp3")
        image_file_path = os.path.join(service.image_dir, f"{song_id}.jpg")

        if os.path.exists(mp3_file_path):
            os.remove(mp3_file_path)
        else:
            raise HTTPException(status_code=404, detail="MP3 file not found")

        if os.path.exists(image_file_path):
            os.remove(image_file_path)
        else:
            raise HTTPException(status_code=404, detail="Image file not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting files: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting files: {e}")

    return {"detail": "Files deleted successfully"}
@app.get("/download/song")
async def download_file(song_id: str):
    """
    :param song_id: The ID of the song to be downloaded.
    :return: Returns a StreamingResponse object that streams the file for download.

    This method is used to download a song file based on its ID. It first checks if the song ID is valid, and then searches for the file location in the music directory. If the file is found
    *, it checks the MD5 checksum of the file against the one stored in the database. If the checksums match, it creates a StreamingResponse object to stream the file for download. The file
    * is streamed in chunks of 64KB.

    If the song ID is invalid or the file is not found, a HTTPException is raised with the appropriate status code (400 or 404). If there is an error retrieving the song information from
    * the database or calculating the MD5 checksum, a HTTPException is raised with a status code of 500.

    The content-disposition header of the response is set to suggest the original file name for download.

    Example usage:

        response = download_file(song_id="123")
        return response
    """
    if song_id is None or song_id == "":
        raise HTTPException(status_code=400, detail="Invalid Request")

    # Find file with song_id, exclude the extension and return any file with that name
    file_location = [f for f in os.listdir(service.music_dir) if f.split(".")[0] == song_id]
    if len(file_location) == 0:
        raise HTTPException(status_code=404, detail="No Songs Found")

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
    try:
        file_md5 = await service.calculate_md5(file_location)

        if file_md5 != md5:
            raise HTTPException(status_code=422, detail="MD5 mismatch")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    """
    :param id: The ID of the image to be downloaded.
    :return: The image file as a FileResponse object.

    The `download_image` method is an asynchronous function that is used to download an image file based on its ID. It takes in a single parameter `id`, which represents the ID of the image
    * to be downloaded.

    The method first checks if the `id` parameter is None. If it is, it raises an HTTPException with a status code of 400 and the detail message "Invalid Request".

    Next, the method attempts to find the file location of the image based on the provided ID. It searches for files in the `service.image_dir` directory and checks if the file's name matches
    * the ID. If no file is found, it raises an HTTPException with a status code of 404 and the detail message "File not found".

    If a matching file is found, the method constructs the full file location path by joining the `service.image_dir` directory path and the file name. It then checks if the image file actually
    * exists at the constructed file location. If the file does not exist, it raises an HTTPException with a status code of 404 and the detail message "Image not found".

    Finally, if all checks pass, the method returns the image file as a FileResponse object, which allows the file to be downloaded by the client.

    Note: This method may raise an HTTPException with a status code of 500 and an error message if any unexpected exceptions occur during the execution of the method.
    """
    if id is None or id == "":
        raise HTTPException(status_code=400, detail="Invalid Request")
    try:
        file_location = [f for f in os.listdir(service.image_dir) if f.split(".")[0] == id]

        if len(file_location) == 0:
            raise HTTPException(status_code=404, detail="No Images Found")

        file_location = os.path.join(service.image_dir, file_location[0])
        if not os.path.exists(file_location):
            raise HTTPException(status_code=404, detail="Image not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FileResponse(file_location)


@app.get("/stop")
async def stop_service():
    """
    Stop Service

    This method stops the service asynchronously and exits the program.

    :return: None
    """
    await service.stop()
    exit(0)