from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse

from repository.timeseries_repository import TimeSeriesRepository


async def get_snapshot_by_uuid_handler(request: Request):
    repository = TimeSeriesRepository()
    snapshot = repository.get_snapshot_by_uuid(request.path_params['uuid'])

    return JSONResponse(snapshot.serialize())


def get_api_routes():
    return [
        Route('/snapshot/get-by-uuid/{uuid}', get_snapshot_by_uuid_handler)
    ]
