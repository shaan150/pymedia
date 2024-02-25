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
    """
    Validate user session.

    :param request: The request object.
    :return: None.
    :raises HTTPException: If the user session is not valid or an error occurs during validation.
    """
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


@app.get("/service_info")
async def get_service_info():
    """
    Get the service info for a given service type.

    :param request: The request object.
    :param service_type: The service type.
    :return: The service info for the given service type.
    :raises HTTPException: If the service type is invalid or an error occurs during the process.
    """
    try:
        return await service.fetch_service_data()
    except Exception as e:
        logger.error(f"Error fetching service data: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error fetching service data")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    :param request: The incoming request object.
    :return: A RedirectResponse object with a status code of 303, redirecting to the "/login" URL.
    """
    return RedirectResponse(url="/login", status_code=303)


@app.get("/home")
async def home(request: Request, _=Depends(validate_user_session)):
    """
    :param request: Request object representing the incoming request
    :param _: User session validation dependency
    :return: TemplateResponse with home.html template, songs list, and error message (if any)
    """
    result = await endpoint_setup(request, "/home")
    if result:
        return result
    error = ''
    try:
        db_service_url = await service.get_service_url(ServiceType.DATABASE_SERVICE)
        file_service_url = await service.get_service_url(ServiceType.FILE_SERVICE)
        # check if this service is best to handle the request
        params = {"username": request.cookies.get('username')}
        req = await service.service_exception_handling(db_service_url, "songs", "GET", params=params)
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
    """
    :param request: The request object containing information about the HTTP request.
    :return: The response object representing the HTML response.

    This method handles the GET request to the "/login" endpoint. It first redirects the request to the optimal service using the `redirect_to_optimal_service` function. Then, it checks
    * if the `auth_token` cookie is present in the request. If the cookie exists, it attempts to validate the user session using the `validate_user_session` function. If the session is valid
    *, it redirects the user to the "/home" page. If the session is not valid, it logs an information message and continues with processing. If there is an exception while validating the
    * user session, it logs an error message.

    If the `auth_token` cookie is not present or the session is invalid, the method renders and returns the "login.html" template. If there is an `error_message` cookie present in the request
    *, it renders the template with the error message and deletes the cookie.

    Note: The `redirect_to_optimal_service` and `validate_user_session` functions are not shown here, but they are assumed to be implemented elsewhere.

    Example usage:
    ```
    response = await login(request)
    ```"""
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
    """
    :param request: Request object containing the HTTP request
    :param username: String representing the username of the user
    :param password: String representing the password of the user
    :return: Returns a response based on the login verification process

    This method is used to verify the login credentials of a user by sending the username and password to
    the authentication service.

    It takes in the following parameters:
    - request: Request object containing the HTTP request
    - username: String representing the username of the user
    - password: String representing the password of the user

    The method performs the following steps:
    1. Checks if the username or password is None. If so, raises an HTTPException with status code 400
       and detail message "Invalid Username or Password, please try again".
    2. Creates a dictionary 'data' with keys 'username' and 'password' which holds the values of the username
       and password parameters.
    3. Retrieves the service URL for the authentication service using the 'get_service_url' method of the 'service'
       object.
    4. Calls the 'service_exception_handling' method of the 'service' object with the service URL, "validate_user",
       "POST", and the 'data' dictionary as parameters. This method handles any exceptions or errors that occur during
       the service call and returns the response.
    5. Checks if the status code of the 'login_response' is 200. If yes, retrieves the 'token' from the response
       and sets cookies 'auth_token' and 'username' with the respective values. Then, redirects the user to the
       "/home" URL with status code 303.
    6. If the status code is not 200, retrieves the detail message from the JSON response and returns a
       TemplateResponse with the "login.html" template, the 'request' parameter, and the error message.
    7. If an HTTPException occurs, handles it by returning a TemplateResponse with the "login.html" template,
       the 'request' parameter, and the error detail from the exception.
    8. If any other exception occurs, handles it by returning a TemplateResponse with the "login.html" template,
       the 'request' parameter, and the string representation of the exception.

    """
    try:
        if username is None or password is None:
            raise HTTPException(status_code=422, detail="Invalid Username Or Password, please try again")
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
            detail = login_response[0]["detail"]
            return templates.TemplateResponse("login.html", {"request": request, "error": detail})

    except HTTPException as http_exception:
        # Handle HTTP exceptions from handle_rest_request
        return templates.TemplateResponse("login.html", {"request": request, "error": http_exception.detail})

    except Exception as e:
        # Handle any other exceptions
        return templates.TemplateResponse("login.html", {"request": request, "error": str(e)})


@app.get("/logout")
async def logout(response: Response):
    """
    :return: The modified response object with cleared cookies and a redirect URL.

    This method is an endpoint for handling user logout. It takes a Response object as a parameter and modifies it to clear the authentication token and username cookies. It then sets the
    * redirect URL to "/login" and returns the modified Response object.

    Example usage:
        response = Response()
        logout(response)

        # The response object now has cleared cookies and a redirect URL.
    """
    # clear the cookies
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("auth_token")
    response.delete_cookie("username")
    return response


@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    """
    Register Endpoint

    :param request: The request object containing information about the HTTP request
    :return: Returns the rendered HTML page for the registration form
    """
    await redirect_to_optimal_service(request, "/register")
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    """
    This method `register_user` is an API endpoint that handles the registration of a user. It receives an HTTP POST request with the following parameters:

    :param request: The incoming HTTP request.
    :param username: The username of the user to be registered. It is a required field.
    :param email: The email address of the user to be registered. It is a required field.
    :param password: The password of the user to be registered. It is a required field.

    :return: Returns a response based on the registration process.

    If any of the required fields (username, email, password) is missing, it raises an HTTPException with a status code 400 and a message "Invalid Details, please try again".

    The method then creates a dictionary `registration_data` containing the provided values: username, email, and password.

    It attempts to fetch the service URL for the authentication service by calling `service.get_service_url(ServiceType.AUTH_SERVICE)`.

    Then it invokes the `service.service_exception_handling` method to make a POST request to the authentication service's "create_user" endpoint, passing the registration data as the request
    * payload.

    If the response status code from the authentication service is 200, the method returns a RedirectResponse to the "/login" URL with a status code 303, indicating a successful registration
    *.

    Otherwise, it extracts the error detail from the response and returns a TemplateResponse, rendering the "register.html" template with the provided request, error detail, and the previously
    * submitted form data (username, email, password).

    If any exception is raised during the process, it gracefully handles the exception and returns a TemplateResponse with the corresponding error message, the request object, and the previously
    * submitted form data (username, email, password).
    """
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
    """
    Parameters:
        request (Request): The request object containing upload data.
        _ (Depends): The dependency to validate the user session.

    Returns:
        TemplateResponse: A TemplateResponse object for "upload.html" template with the request object.
    """
    result = await endpoint_setup(request, "/upload/song")
    if result:
        return result

    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload/song")
async def upload_song(request: Request, _=Depends(validate_user_session), song_name: str = Form(...),
                      artist: str = Form(...),
                      image: UploadFile = File(...), mp3_file: UploadFile = File(...)):
    """
    :param request: The request object of the current HTTP request.
    :param _: A dependency to validate the user session.
    :param song_name: The name of the song being uploaded.
    :param artist: The name of the artist of the song being uploaded.
    :param image: The image file of the song being uploaded.
    :param mp3_file: The MP3 file of the song being uploaded.
    :return: A redirect response to the home page if the upload is successful, otherwise a template response with an error detail.

    Uploads a song to the server.

    This method handles the process of uploading a song to the server. It expects a request object, a user session validation dependency, the name of the song, the artist name, an image
    * file, and an MP3 file as parameters. The method returns a redirect response to the home page if the upload is successful, otherwise it returns a template response with an error detail
    *.

    The method performs the following steps:
    1. Validates the user session by using the dependency.
    2. Checks if the song name, image file, and MP3 file are not None. If any of them is None, it raises an HTTPException with a status code of 400 and the detail "Invalid Details, please
    * try again".
    3. Checks if the image file is in the "image/jpeg" or "image/png" format. If not, it raises an HTTPException with a status code of 400 and the detail "Invalid Image File Type".
    4. Checks if the MP3 file is in the "audio/mpeg" format. If not, it raises an HTTPException with a status code of 400 and the detail "Invalid Audio File Type".
    5. Retrieves the service URLs for the database and file services.
    6. Generates a unique ID for the song.
    7. Calculates the MD5 hash of the MP3 file by calling the `service.calculate_md5` function (assuming it is an async function).
    8. Creates a dictionary representing the song with the song ID, song name, artist name, MD5 hash, and username.
    9. Makes an API call to the database service to create the song using the `service.service_exception_handling` function.
    10. Reads the contents of the image file and MP3 file.
    11. Resets the pointers of the image file and MP3 file.
    12. Constructs a files dictionary with the image file and MP3 file contents.
    13. Constructs a data dictionary with the song ID.
    14. Makes an API call to the file service to upload the song using the `service.service_exception_handling` function.
    15. Creates a redirect response to the home page with the status code 303.
    16. Retrieves the auth token and username from the request cookies.
    17. Sets the auth token and username as cookies in the redirect response.
    18. Returns the redirect response.

    If an HTTPException is raised with a status code of 401, the method returns a redirect response to the login page with the status code 303. Otherwise, if an exception other than HTTP
    *Exception is raised, the method returns a template response with the error message converted to a string.

    Example usage:
        response = upload_song(request, validate_user_session, "Song Name", "Artist", image_file, mp3_file)
    """
    try:
        username = request.cookies.get('username')
        # Attempt to validate the user session

        if song_name is None or image is None or mp3_file is None:
            raise HTTPException(status_code=400, detail="Invalid Details, please try again")

        if image.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=422, detail="Invalid Image File Type")

        if mp3_file.content_type != "audio/mpeg":  # Correct MIME type for MP3 files
            raise HTTPException(status_code=422, detail="Invalid Audio File Type")

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
        # get name of the files with extension
        image_name = image.filename
        mp3_name = mp3_file.filename

        # Make sure service_exception_handling can handle file uploads correctly
        files = {
            "image_file": (image_name, image_content, image.content_type),
            "mp3_file": (mp3_name, mp3_content, mp3_file.content_type)
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

@app.get("/services")
async def manage_services(request: Request, _=Depends(validate_user_session)):
    """
    :param request: The HTTP request object.
    :param _: The user session validation dependency.
    :return: A template response object.

    This method is used to manage services. It retrieves a list of services from the main service URL and filters out the current service. The resulting services are then rendered using
    * the "services.html" template.

    The method first calls the "endpoint_setup" function to prepare for making a request to the "/services" endpoint. If the result of the setup is not empty, it is returned immediately
    *.

    Next, the method attempts to retrieve the services by making a request to the main service URL using the "service_exception_handling" function. The services are extracted from the response
    * and filtered to exclude the current service based on the URL. The resulting services list is assigned to the "services" variable.

    If an exception occurs during the retrieval of services, the error message is appended to the "error" variable.

    Finally, a template response is returned with the "services.html" template, along with the request, services, and error as context variables.

    Example usage:

        result = await manage_services(request, _)

    """
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
    """
    :param request: The incoming HTTP request.
    :param _: Dummy parameter for dependency injection.
    :return: A TemplateResponse object.

    This method is an HTTP GET route handler for "/service/create". It creates a service and renders the "create_service.html"
    template with the necessary information.

    The parameters are:
    - request: The incoming HTTP request object.
    - _: Dummy parameter used for dependency injection.

    The method returns a TemplateResponse object.

    Example usage:

    response = await create_service(request, _)
    """
    result = await endpoint_setup(request, "/service/create")
    if result:
        return result
    error = ''

    service_types = [(type.name, type.value) for type in ServiceType if type not in [ServiceType.DATABASE_SERVICE,
                                                                                     ServiceType.FILE_SERVICE,
                                                                                     ServiceType.MAIN_SERVICE]]

    return templates.TemplateResponse("create_service.html",
                                      {"request": request, "error": error, "service_types": service_types})


@app.post("/service/create")
async def create_service(request: Request, _=Depends(validate_user_session), service_type: ServiceType = Form(...)):
    """
    Creates a new service.

    :param request: The request object.
    :param _: A dependency function for validating user session.
    :param service_type: The type of service to create.
    :return: A RedirectResponse object if the service is created successfully, or a TemplateResponse object if there is an error.
    :raises HTTPException: If there is an HTTP exception when starting the service.
    """
    try:
        await service_utils.start_service(service.main_service_url, service_type)
        return RedirectResponse(url="/services", status_code=303)
    except HTTPException as e:
        return templates.TemplateResponse("create_service.html", {"request": request, "error": e.detail})
    except Exception as e:
        return templates.TemplateResponse("create_service.html", {"request": request, "error": str(e)})


@app.get("/songs")
async def get_songs(request: Request, _=Depends(validate_user_session)):
    """
    Fetches songs from the database service, adds URLs for song and image download,
    and returns the songs rendered in a template response.

    :param request: The request object containing information about the HTTP request.
    :param _: The dependency object for validating user session.
    :return: A TemplateResponse object with the rendered songs, request, and error (if any).
    """
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
        if e.status_code != 404 and e.status_code != 400:
            logger.debug(f"Error getting songs: {e.detail}")
            error += f"\nError getting songs: {e.detail}"
        return templates.TemplateResponse("songs.html", {"request": request, "error": error, "songs": []})
    except Exception as e:
        error += f"\nSystem Error: {e}"
        return templates.TemplateResponse("songs.html", {"request": request, "error": error})


@app.post("/start_service")
async def start_service(request: Request):
    """
    Start Service

    This method is used to start a service based on the given request.

    Parameters:
        request (Request): The request object containing the necessary information to start the service.

    Returns:
        None

    """
    await start_service_endpoint(request)


@app.delete("/stop")
async def stop_service():
    """
    Stop Service

    This method stops the service by calling the `stop()` method on the `service` object and exits the program.

    :return: None
    """
    await service.stop()
    exit(0)


@app.delete("/stop_service")
async def stop_service(service_url):
    """
    Stop the service.

    :param service_url: The URL of the service to stop.
    :return: A dictionary indicating the status of the service stop operation.
    """
    try:
        await service.service_exception_handling(service_url, "stop", "DELETE")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping service: {e}")
        raise HTTPException(status_code=500, detail=f"Error stopping service: {e}")
    return {"status": "Service Stopped"}


@app.get("/error", response_class=HTMLResponse)
async def error(request: Request):
    """
    :param request: The request object containing information about the HTTP request.
    :return: A TemplateResponse object with the rendered error message.

    This method is used to handle error messages. It retrieves the error message from the request cookies and renders the "error.html" template with the error message.

    Example usage:
    ```
    response = await error(request)
    ```

    """
    error_message = request.cookies.get('error_message')
    if error_message:
        response = templates.TemplateResponse("error.html", {"request": request, "error": error_message})
        response.delete_cookie("error_message")
        return response
    return templates.TemplateResponse("error.html", {"request": request})


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Custom HTTP exception handler.

    :param request: The request object.
    :type request: starlette.requests.Request
    :param exc: The exception object.
    :type exc: starlette.exceptions.HTTPException
    :return: The response object.
    :rtype: starlette.responses.Response

    """
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # Handle unauthorized error, potentially redirecting
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    redirect_response = RedirectResponse(url="/error", status_code=303)
    redirect_response.set_cookie(key="error_message", value=exc.detail, httponly=True)
    return redirect_response


async def redirect_to_optimal_service(request: Request, endpoint: Optional[str] = None):
    """
    Redirects the request to the optimal service URL.

    :param request: The request object.
    :type request: Request
    :param endpoint: The optional endpoint to append to the optimal service URL.
    :type endpoint: Optional[str]
    :return: The redirect response object or None if no redirection is required.
    :rtype: RedirectResponse or None
    """
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
    """
    :param request: The incoming request object.
    :param endpoint: The endpoint string that the request is being sent to.
    :return: The response if a redirect to the optimal service is necessary, otherwise None.
    """
    # Attempt to redirect to the optimal service if necessary
    response = await redirect_to_optimal_service(request, endpoint)
    if response:
        return response

@app.post("/start_service")
async def start_service(request: Request):
    """
    :param request: The request object containing the client's request data.
    :return: None

    This method is a POST endpoint that starts a service. It takes a request object as a parameter and does not have a return value.
    The method tries to execute the start_service_endpoint function with the provided request. If an HTTPException is raised, it is re-raised.
    If any other exception is raised, it is caught, and a new HTTPException with a 500 status code and the exception message as the detail is raised.
    """
    try:
        await start_service_endpoint(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))