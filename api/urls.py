from django.urls import path
from .import views
urlpatterns = [
    path('stock/predict/',views.StockPredictionAPIView.as_view()),
    
]
