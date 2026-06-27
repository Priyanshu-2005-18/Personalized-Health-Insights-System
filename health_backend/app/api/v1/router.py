from fastapi import APIRouter

from app.api.v1 import auth, users, health, sleep, activity, nutrition, insights, predict, recommendations

api_router = APIRouter()

api_router.include_router(auth.router,            prefix="/auth",            tags=["Authentication"])
api_router.include_router(users.router,           prefix="/users",           tags=["Users"])
api_router.include_router(health.router,          prefix="/health",          tags=["Health Logs"])
api_router.include_router(sleep.router,           prefix="/sleep",           tags=["Sleep"])
api_router.include_router(activity.router,        prefix="/activity",        tags=["Activity"])
api_router.include_router(nutrition.router,       prefix="/nutrition",       tags=["Nutrition"])
api_router.include_router(insights.router,        prefix="/insights",        tags=["Insights"])
api_router.include_router(predict.router,         prefix="/predict",         tags=["Health Score Prediction"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])

