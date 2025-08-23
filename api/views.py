from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score
from .serializers import StockPredictionSerializer
from .utils import save_plot

model = None  # Global model cache


class StockPredictionAPIView(APIView):
    def post(self, request):
        global model

        # Dynamically import and configure matplotlib
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        serializer = StockPredictionSerializer(data=request.data)
        if serializer.is_valid():
            ticker = serializer.validated_data['ticker']

            now = datetime.now()
            start = datetime(now.year - 10, now.month, now.day)
            end = now

            try:
                df = yf.download(ticker, start, end)
            except Exception as e:
                return Response({"error": f"Failed to fetch stock data: {e}"}, status=500)

            if df.empty:
                return Response({"error": "No data found for given ticker."}, status=status.HTTP_404_NOT_FOUND)

            df = df.reset_index()

            # Plot 1: Closing Price
            plt.figure(figsize=(14, 6))
            plt.plot(df['Close'], label='Closing Price')
            plt.title(f'Closing Price of {ticker}')
            plt.xlabel('Days')
            plt.ylabel('Price')
            plt.legend()
            plot_img = save_plot(f'{ticker}_plot.png')

            # Plot 2: 100-DMA
            da100 = df['Close'].rolling(100).mean()
            plt.figure(figsize=(14, 6))
            plt.plot(df['Close'], label='Closing Price')
            plt.plot(da100, label='100 DMA')
            plt.title(f'100-Day Moving Average of {ticker}')
            plt.xlabel('Days')
            plt.ylabel('Price')
            plt.legend()
            plot_img_100dma = save_plot(f'{ticker}_100dma_plot.png')

            # Plot 3: 200-DMA
            da200 = df['Close'].rolling(200).mean()
            plt.figure(figsize=(14, 6))
            plt.plot(df['Close'], label='Closing Price')
            plt.plot(da100, 'r', label='100 DMA')
            plt.plot(da200, 'g', label='200 DMA')
            plt.title(f'200-Day Moving Average of {ticker}')
            plt.xlabel('Days')
            plt.ylabel('Price')
            plt.legend()
            plot_img_200dma = save_plot(f'{ticker}_200dma_plot.png')

            # Data preparation
            data_training = df['Close'][0:int(len(df) * 0.70)]
            data_testing = df['Close'][int(len(df) * 0.70):]
            scaler = MinMaxScaler(feature_range=(0, 1))

            # Lazy load model once
            if model is None:
                try:
                    from keras.models import load_model
                    model = load_model('stock_prediction_model.keras')
                except Exception as e:
                    return Response({"error": f"Model load failed: {e}"}, status=500)

            past_100_days = data_training.tail(100)
            final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
            input_data = scaler.fit_transform(final_df.values.reshape(-1, 1))

            x_test, y_test = [], []
            for i in range(100, len(input_data)):
                x_test.append(input_data[i - 100:i])
                y_test.append(input_data[i, 0])

            x_test = np.array(x_test)
            y_test = np.array(y_test)

            y_predicted = model.predict(x_test, verbose=0)
            y_predicted = scaler.inverse_transform(y_predicted.reshape(-1, 1)).flatten()
            y_test = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()

            # Plot 4: Final Prediction
            plt.figure(figsize=(12, 5))
            plt.plot(y_test, 'b', label='Original Price', linewidth=2)
            plt.plot(y_predicted, 'r', label='Predicted Price', alpha=0.6)
            plt.title(f'Final Prediction for {ticker}')
            plt.xlabel('Days')
            plt.ylabel('Price')
            plt.legend()
            plot_prediction = save_plot(f'{ticker}_final_prediction.png')

            # Metrics
            mse = mean_squared_error(y_test, y_predicted)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, y_predicted)

            return Response({
                'status': 'success',
                'plot_img': plot_img,
                'plot_img_100dma': plot_img_100dma,
                'plot_img_200dma': plot_img_200dma,
                'plot_prediction': plot_prediction,
                'mse': mse,
                'rmse': rmse,
                'r2': r2
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
