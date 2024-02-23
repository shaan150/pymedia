from fastapi import HTTPException, Request, Depends

from classes.enum.ServiceType import ServiceType
from classes.services.MainService import MainService
from classes.ServiceInfo import ServiceInfo

service = MainService()
app = service.app


@app.get("/")
async def root():
    return {"detail": "Main Server Active"}


@app.get("/debug")
async def debug():
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
    return {"services": [service.to_dict() for service in service.services.values()]}


@app.get("/secret_key")
async def get_secret_key(_=Depends(service.verify_ip)):
    return {"secret_key": service.secret_key}


@app.post("/update_or_add_service")
async def update_service(request: Request):
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


@app.get("/database_connection")
async def database_connection():
    """
    Endpoint to retrieve the database connection string.
    """
    if not service.db_service_url:
        raise HTTPException(status_code=404, detail="Database URL not configured")
    return {"database_url": service.db_service_url}
