import os
import os
import time
from typing import Optional

from fastapi import Form, Request, Response, HTTPException, UploadFile, File, status, Depends
from fastapi.exceptions import StarletteHTTPException
from fastapi.logger import logger
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from classes.enum.ServiceType import ServiceType
from classes.services.ClientService import ClientService
from utils import service_utils
from utils.service_utils import start_service_endpoint

service = ClientService()
templates = Jinja2Templates(directory="templates")

app = service.app


async def validate_user_session(request: Request):
    token: Optional[str] = request.cookies.get('auth_token')
    username: Optional[str] = request.cookies.get('username')

    if username is None or token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authenticated")

    try:
        service_url = await service.get_service_url(ServiceType.AUTH_SERVICE)
        # Assuming service.service_exception_handling properly raises HTTPException on failure
        await service.service_exception_handling(service_url, "validate_token", "GET",
                                                 params={"username": username, "token": token})
    except HTTPException as e:
        if e.status_code == 401:
            # Clear the cookies
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authenticated")
        # Re-raise the HTTPException with specific detail or simply propagate it
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    except Exception as e:
        logger.error(f"Error validating user session: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error validating user session")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/login", status_code=303)


@app.get("/home")
async def home(request: Request, _=Depends(validate_user_session)):
    result = await endpoint_setup(request, "/home")
    if result:
        return result
    error = ''

    try:
        db_service_url = await service.get_service_url(ServiceType.DATABASE_SERVICE)
        file_service_url = await service.get_service_url(ServiceType.FILE_SERVICE)
        # check if this service is best to handle the request

        req = await service.service_exception_handling(db_service_url, "songs", "GET")
        songs = req[0]
        for song in songs:
            song_id = song.get("song_id")
            song["song_url"] = f"http://{file_service_url}/download/song?song_id={song_id}"
            song["image_url"] = f"http://{file_service_url}/download/image?id={song_id}"

        return templates.TemplateResponse("home.html", {"request": request, "songs": songs, "error": error})
    except HTTPException as e:
        if e.status_code != 404 and e.status_code != 400:
            logger.debug(f"Error getting playlists: {e.detail}")
            error += f"\nError getting playlists: {e.detail}"

        return templates.TemplateResponse("home.html", {"request": request, "error": error})
    except Exception as e:
        error += f"\nSystem Error: {e}"
        return templates.TemplateResponse("home.html", {"request": request, "error": error})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    await redirect_to_optimal_service(request)
    if request.cookies.get('auth_token') is not None:
        try:
            await validate_user_session(request)
            return RedirectResponse(url="/home", status_code=303)
        except HTTPException:
            logger.info("No Valid Session Found, Redirecting to Login Page")
        except Exception as e:
            logger.error(f"Error validating user session: {e}")

    response = templates.TemplateResponse("login.html", {"request": request})
    error = request.cookies.get('error_message')

    if error:
        response = templates.TemplateResponse("login.html", {"request": request, "error": error})
        response.delete_cookie("error_message")

    return response


@app.post("/login")
async def login_verify(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        if username is None or password is None:
            raise HTTPException(status_code=400, detail="Invalid Username Or Password, please try again")

        data = {"username": username, "password": password}
        service_url = await service.get_service_url(ServiceType.AUTH_SERVICE)
        login_response = await service.service_exception_handling(service_url, "validate_user", "POST", data=data)

        if login_response[1] == 200:
            token = login_response[0].get("token")
            if token:
                redirect_response = RedirectResponse(url="/home", status_code=303)  # Use 303 for HTTP POST redirects
                redirect_response.set_cookie(key="auth_token", value=token, httponly=True)
                redirect_response.set_cookie(key="username", value=username, httponly=True)
                return redirect_response
            else:
                return templates.TemplateResponse("login.html",
                                                  {"request": request, "error": "Login failed. Please try again."})
        else:
            detail = login_response.json().get("detail", "Invalid credentials")
            return templates.TemplateResponse("login.html", {"request": request, "error": detail})

    except HTTPException as http_exception:
        # Handle HTTP exceptions from handle_rest_request
        return templates.TemplateResponse("login.html", {"request": request, "error": http_exception.detail})

    except Exception as e:
        # Handle any other exceptions
        return templates.TemplateResponse("login.html", {"request": request, "error": str(e)})


@app.get("/logout")
async def logout(response: Response):
    # clear the cookies
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("auth_token")
    response.delete_cookie("username")
    return response


@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    await redirect_to_optimal_service(request, "/register")
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if username is None or email is None or password is None:
        raise HTTPException(status_code=400, detail="Invalid Details, please try again")

    registration_data = {
        "username": username,
        "email": email,
        "password": password
    }

    try:
        service_url = await service.get_service_url(ServiceType.AUTH_SERVICE)
        register_response = await service.service_exception_handling(service_url, "create_user", "POST",
                                                                     data=registration_data)

        if register_response[1] == 200:
            return RedirectResponse(url="/login", status_code=303)
        else:
            detail = register_response.json().get("detail", "Unable to register at this time")
            return templates.TemplateResponse("register.html", {"request": request, "error": detail})

    except HTTPException as e:
        return templates.TemplateResponse("register.html", {"request": request, "error": e.detail, "username": username,
                                                            "email": email, "password": password})
    except Exception as e:
        return templates.TemplateResponse("register.html", {"request": request, "error": str(e), "username": username,
                                                            "email": email, "password": password})


@app.get("/upload/song", response_class=HTMLResponse)
async def upload_song(request: Request, _=Depends(validate_user_session)):
    result = await endpoint_setup(request, "/upload/song")
    if result:
        return result

    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload/song")
async def upload_song(request: Request, _=Depends(validate_user_session), song_name: str = Form(...),
                      artist: str = Form(...),
                      image: UploadFile = File(...), mp3_file: UploadFile = File(...)):
    try:
        username = request.cookies.get('username')
        # Attempt to validate the user session

        if song_name is None or image is None or mp3_file is None:
            raise HTTPException(status_code=400, detail="Invalid Details, please try again")

        if image.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid Image File Type")

        if mp3_file.content_type != "audio/mpeg":  # Correct MIME type for MP3 files
            raise HTTPException(status_code=400, detail="Invalid Audio File Type")

        db_service_url = await service.get_service_url(ServiceType.DATABASE_SERVICE)
        file_service_url = await service.get_service_url(ServiceType.FILE_SERVICE)

        # Generate a unique ID for the song
        song_id = f"sg_{int(time.time() * 1000)}_{os.urandom(6).hex()}"

        # Assuming 'calculate_md5' is an async function you've implemented
        md5 = await service.calculate_md5(mp3_file)
        song = {"song_id": song_id, "song_name": song_name, "artist": artist, "md5": md5, "username": username}

        await service.service_exception_handling(db_service_url, "songs/song/create", "POST", data=song)
        # Read the file contents and reset the pointers if needed
        image_content = await image.read()
        mp3_content = await mp3_file.read()
        await image.seek(0)
        await mp3_file.seek(0)

        # Make sure service_exception_handling can handle file uploads correctly
        files = {
            "image_file": ("image_filename.png", image_content, image.content_type),
            "mp3_file": ("mp3_filename.mp3", mp3_content, mp3_file.content_type)
        }
        data = {"song_id": song_id}
        await service.service_exception_handling(file_service_url, "upload/song", "PUT", params=data, files=files)
        redirect_response = RedirectResponse(url="/home", status_code=303)
        # get token and username from request

        token = request.cookies.get('auth_token')
        username = request.cookies.get('username')

        redirect_response.set_cookie(key="auth_token", value=token, httponly=True)
        redirect_response.set_cookie(key="username", value=username, httponly=True)
        return redirect_response

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/login", status_code=303)
        return templates.TemplateResponse("upload.html", {"request": request, "error": e.detail})
    except Exception as e:
        return templates.TemplateResponse("upload.html", {"request": request, "error": str(e)})



"""@app.get("/upload/playlist", response_class=HTMLResponse)
async def upload_playlist(request: Request, _=Depends(validate_user_session)):
    result = await endpoint_setup(request, "/upload/playlist")
    if result:
        return result

    try:
        current_song = await retrieve_song(request)
        return templates.TemplateResponse("create_playlist.html", {"request": request, "current_song": current_song})
    except Exception as e:
        return templates.TemplateResponse("create_playlist.html", {"request": request, "error": str(e)})


@app.post("/upload/playlist")
async def upload_playlist(request: Request, _=Depends(validate_user_session), playlist_name: str = Form(...),
                          image: UploadFile = File(...)):
    try:

        if playlist_name is None or image is None:
            raise HTTPException(status_code=400, detail="Invalid Details, please try again")

        if image.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid Image File Type")

        db_service_url = await service.get_service_url(ServiceType.DATABASE_SERVICE)
        file_service_url = await service.get_service_url(ServiceType.FILE_SERVICE)

        username = request.cookies.get('username')
        # Generate a unique ID for the song
        playlist_id = f"pl_{int(time.time() * 1000)}_{os.urandom(6).hex()}"
        playlist = {"playlist_id": playlist_id, "playlist_name": playlist_name, "username": username}

        await service.service_exception_handling(db_service_url, "playlists/playlist/create", "POST", data=playlist)

        # Read the file contents and reset the pointers if needed
        image_content = await image.read()
        await image.seek(0)

        params = {"playlist_id": playlist_id}
        # Make sure service_exception_handling can handle file uploads correctly
        files = {
            "image_file": ("image_filename.png", image_content, image.content_type),
        }
        await service.service_exception_handling(file_service_url, "upload/playlist", "PUT", params=params, files=files)
        redirect_response = RedirectResponse(url="/home", status_code=303)

        token = request.cookies.get('auth_token')
        username = request.cookies.get('username')
        song_id = request.cookies.get('song_id')

        redirect_response.set_cookie(key="auth_token", value=token, httponly=True)
        redirect_response.set_cookie(key="username", value=username, httponly=True)
        redirect_response.set_cookie(key="song_id", value=song_id, httponly=True)
        return redirect_response

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/login", status_code=303)
        return templates.TemplateResponse("create_playlist.html", {"request": request, "error": e.detail})
    except Exception as e:
        return templates.TemplateResponse("create_playlist.html", {"request": request, "error": str(e)})
"""

@app.get("/songs/song")
async def get_song(request: Request, song_id: str, _=Depends(validate_user_session)):
    result = await endpoint_setup(request, "/songs/song")
    if result:
        return result
    error = ''

    try:

        db_service_url = await service.get_service_url(ServiceType.DATABASE_SERVICE)
        file_service_url = await service.get_service_url(ServiceType.FILE_SERVICE)

        song_info = await service.service_exception_handling(db_service_url, "songs/song", "GET",
                                                             params={"song_id": song_id})
        song = f"http://{file_service_url}/download/song?song_id={song_id}"

        return templates.TemplateResponse("song.html", {"request": request, "song_info": song_info, "song": song})
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/login", status_code=303)
        error += f"\nError getting song: {e.detail}"
        return templates.TemplateResponse("song.html", {"request": request, "error": error})
    except Exception as e:
        error += f"\nSystem Error: {e}"
        return templates.TemplateResponse("song.html", {"request": request, "error": error})


@app.get("/services")
async def manage_services(request: Request, _=Depends(validate_user_session)):
    result = await endpoint_setup(request, "/services")
    if result:
        return result
    error = ''

    try:
        req = await service.service_exception_handling(service.main_service_url, "get_services", "GET")
        services = req[0].get("services")
        # filter out the current service
        services = [serv for serv in services if serv.get("url") != service.service_url]
        return templates.TemplateResponse("services.html", {"request": request, "services": services, "error": error})
    except Exception as e:
        error += f"\nError getting services: {e}"
        return templates.TemplateResponse("services.html", {"request": request, "error": error})


@app.get("/service/create")
async def create_service(request: Request, _=Depends(validate_user_session)):
    result = await endpoint_setup(request, "/service/create")
    if result:
        return result
    error = ''

    service_types = [(type.name, type.value) for type in ServiceType if type not in [ServiceType.DATABASE_SERVICE,
                                                                                     ServiceType.FILE_SERVICE,
                                                                                     ServiceType.MAIN_SERVICE]]

    return templates.TemplateResponse("create_service.html", {"request": request, "error": error, "service_types": service_types})


@app.post("/service/create")
async def create_service(request: Request, _=Depends(validate_user_session), service_type: ServiceType = Form(...)):
    try:
        await service_utils.start_service(service.main_service_url, service_type)
        return RedirectResponse(url="/services", status_code=303)
    except HTTPException as e:
        return templates.TemplateResponse("create_service.html", {"request": request, "error": e.detail})
    except Exception as e:
        return templates.TemplateResponse("create_service.html", {"request": request, "error": str(e)})


@app.get("/songs")
async def get_songs(request: Request, _=Depends(validate_user_session)):
    error = ''

    res = await endpoint_setup(request, "/songs")
    if res:
        return res

    try:
        db_service_url = await service.get_service_url(ServiceType.DATABASE_SERVICE)
        file_service_url = await service.get_service_url(ServiceType.FILE_SERVICE)

        req = await service.service_exception_handling(db_service_url, "songs", "GET")
        songs = req[0]
        for song in songs:
            song_id = song.get("song_id")
            song["song_url"] = f"http://{file_service_url}/download/song?song_id={song_id}"
            song["image_url"] = f"http://{file_service_url}/download/image?id={song_id}"

        return templates.TemplateResponse("songs.html", {"request": request, "songs": songs, "error": error})
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/login", status_code=303)
        error += f"\nError getting songs: {e.detail}"
        return templates.TemplateResponse("songs.html", {"request": request, "error": error})
    except Exception as e:
        error += f"\nSystem Error: {e}"
        return templates.TemplateResponse("songs.html", {"request": request, "error": error})


@app.post("/start_service")
async def start_service(request: Request):
    await start_service_endpoint(request)


@app.delete("/stop")
async def stop_service():
    await service.stop()
    exit(0)


@app.delete("/stop_service")
async def stop_service(service_url):
    try:
        await service.service_exception_handling(service_url, "stop", "DELETE", params={"service_url": service_url})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping service: {e}")
        raise HTTPException(status_code=500, detail=f"Error stopping service: {e}")
    return {"status": "Service Stopped"}


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # Handle unauthorized error, potentially redirecting
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # For other HTTP exceptions, return a generic JSON response or customize as needed
    return JSONResponse(content={"error": exc.detail}, status_code=exc.status_code)


async def redirect_to_optimal_service(request: Request, endpoint: Optional[str] = None):
    optimal_service = await service.is_optimal_service()
    if optimal_service != service.service_url:
        if endpoint:
            optimal_service += endpoint

        optimal_service = f"http://{optimal_service}"

        # save the current cookie values
        token = request.cookies.get('auth_token')
        username = request.cookies.get('username')
        error_message = request.cookies.get('error_message')

        response_redirect = RedirectResponse(url=optimal_service, status_code=303)
        # Set cookies on the response object
        response_redirect.set_cookie(key="auth_token", value=token, httponly=True)
        response_redirect.set_cookie(key="username", value=username, httponly=True)
        response_redirect.set_cookie(key="error_message", value=error_message, httponly=True)

        return response_redirect
    return None


async def endpoint_setup(request: Request, endpoint: str):
    # Attempt to redirect to the optimal service if necessary
    response = await redirect_to_optimal_service(request, endpoint)
    if response:
        return response