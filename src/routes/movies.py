import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from database import get_db, MovieModel
from schemas import MovieListResponseSchema, MovieDetailResponseSchema
from schemas.errors import NotFoundResponse

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={
        404: {
            "model": NotFoundResponse,
            "description": "No movies found.",
            "content": {
                "application/json": {"example": {"detail": "No movies found."}}
            },
        },
    },
)
async def movies_list(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    total_pages = math.ceil(total_items / per_page)
    if total_items == 0 or page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")
    prev_page = (
        str(request.url.replace_query_params(page=(page - 1), per_page=per_page))
        if page > 1
        else None
    )
    next_page = (
        str(request.url.replace_query_params(page=(page + 1), per_page=per_page))
        if page < total_pages
        else None
    )
    result = await db.execute(
        select(MovieModel).offset((page - 1) * per_page).limit(per_page)
    )
    return MovieListResponseSchema(
        movies=[
            MovieDetailResponseSchema.model_validate(movie)
            for movie in result.scalars().all()
        ],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema,
    responses={
        404: {
            "model": NotFoundResponse,
            "description": "Movie with the given ID was not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
    },
)
async def movies_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))

    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return MovieDetailResponseSchema.model_validate(movie)
