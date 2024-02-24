from fastapi import HTTPException, Request, Depends

from classes.enum.ServiceType import ServiceType
from classes.services.MainService import MainService
from classes.ServiceInfo import ServiceInfo

service = MainService()
app = service.app


@app.get("/")
async def root():
    """
    Returns the main server status.

    :return: A dictionary containing the server status.
    :rtype: dict
    """
    return {"detail": "Main Server Active"}


@app.get("/debug")
async def debug():
    """
    :return: A dictionary containing the following information:
        - "services": A dictionary representing the services along with their details. Each service is represented by its URL and contains the following information:
            - "name": The name of the service.
            - "other_details": A dictionary containing additional details of the service. This can be obtained by calling the 'to_dict()' method on the 'service_info' object if it exists
    *, otherwise an empty dictionary.
        - "services_with_scores": A dictionary mapping the URLs of the services to their respective scores.
        - "services_with_availability": A dictionary mapping the URLs of the services to their respective availability scores.

    """
    services = service.services
    services_with_scores = {}
    services_with_availability = {}

    for url, service_info in services.items():
        score = await service_info.calc_score()  # Assuming this is an async method
        availability = await service_info.calc_available_score()  # Assuming this is an async method
        services_with_scores[url] = score
        services_with_availability[url] = availability

    # For serializing the services, assuming ServiceInfo objects are not directly serializable
    services_data = {
        url: {
            "name": service_info.name,
            # Assuming you have a method or logic to serialize service_info to a dictionary
            "other_details": service_info.to_dict() if hasattr(service_info, 'to_dict') else {}
        } for url, service_info in services.items()
    }

    return {
        "services": services_data,
        "services_with_scores": services_with_scores,
        "services_with_availability": services_with_availability
    }


@app.get("/get_service")
async def get_service(service_type: ServiceType):
    """
    Gets the optimal service based on the provided service type.

    :param service_type: The type of service to retrieve.
    :type service_type: ServiceType
    :return: The optimal service for the given service type.
    :rtype: Service
    :raises HTTPException: If the request is invalid or no service is found.
    """
    if service_type is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    # get all services with type auth_service
    try:
        optimal_service = await service.get_service(service_type)
        if optimal_service is None:
            raise HTTPException(status_code=404, detail=f"No {service_type} service found")
        return optimal_service
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error Handling Endpoint {str(e)}")

@app.get("/get_services")
async def get_services(_ = Depends(service.verify_ip)):
    """
        Retrieve the services.

        :param _: The IP verification dependency.
        :return: A dictionary containing the services.
    """
    return {"services": [service.to_dict() for service in service.services.values()]}


@app.get("/secret_key")
async def get_secret_key(_=Depends(service.verify_ip)):
    """
    :param _: This parameter is ignored and does not have any effect on the method. It is used to satisfy the Depends dependency in FastAPI.

    :return: This method returns a dictionary containing the secret key. The key is "secret_key" and its value is obtained from the `service.secret_key`.
    """
    return {"secret_key": service.secret_key}


@app.post("/update_or_add_service")
async def update_service(request: Request):
    """
    Updates or adds a service.

    :param request: The request containing the service information.
    :return: A dictionary with a detail message indicating if the service was updated or added successfully.
    :raises HTTPException: If the request is invalid or there is an error updating or adding the service.
    """
    if request is None:
        raise HTTPException(status_code=400, detail="Invalid Request")

    try:
        data = await request.json()

        if not data:
            raise Exception()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid Request, Please provide a valid JSON body")

    # Extract service data from the request
    required_fields = ["name", "type", "url"]
    if not all(field in data for field in required_fields):
        raise HTTPException(status_code=400, detail="Insufficient service data")

    name = data["name"]
    service_type = data["type"]
    url = data["url"]
    cpu_usage = data.get("cpu_usage", 0)
    memory_usage = data.get("memory_usage", 0)
    memory_free = data.get("memory_free", 0)
    cpu_free = data.get("cpu_free", 0)
    total_memory = data.get("total_memory", 0)

    service_info = ServiceInfo(name, service_type, url, cpu_usage, memory_usage, memory_free, total_memory, cpu_free)

    try:
        await service.update_or_add_service(service_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"detail": f"Service {name} Updated"}


@app.delete("/remove_service/{service_url}")
async def remove_service(service_url: str):
    """
    :param service_url: The URL of the service to be removed.
    :return: A dictionary containing the detail of the removal operation.

    This method is used to remove a service by its URL. It sends a DELETE request to the '/remove_service/{service_url}' endpoint.

    Example usage:
        response = await remove_service('http://example.com/service1')

    The method first checks if a service URL is provided. If not, it raises an HTTPException with a status code 400 and a detail message indicating the lack of a service URL.

    Next, it tries to call the 'del_service' function from the 'service' module passing the service URL as an argument. If an HTTPException with a status code different from 404 is raised
    *, it is re-raised.

    If any other exception is raised during the deletion process, an HTTPException with a status code 500 is raised with a detail message indicating the failure.

    If the deletion is successful, the method returns a dictionary with a detail message indicating the successful removal of the service at the specified URL.

    Note: URL decoding might be required depending on how the URL is passed. The 'urllib.parse.unquote(service_url)' function can be used for decoding if needed.
    """
    # URL decoding might be necessary depending on how you pass the URL
    # You can use urllib.parse.unquote(service_url) if needed

    if not service_url:
        raise HTTPException(status_code=400, detail="No Service URL Provided")

    try:
        # Assuming del_service function accepts the service URL and performs deletion
        await service.del_service(service_url)
    except HTTPException as e:
        if e.status_code != 404:
            raise
    except Exception as e:
        # It's good practice to log the actual error for debugging purposes
        raise HTTPException(status_code=500, detail="Failed to remove the service with error: " + str(e))

    return {"detail": f"Service at {service_url} removed successfully"}
