from rest_framework import views
from rest_framework.response import Response
from keras.models import load_model
import numpy as np
from keras.utils import load_img,img_to_array
import streamlit as st
import urllib3
from .serializers import PlantPredictionSerializer
from PIL import Image
import io
from dotenv import load_dotenv
import os
import openai
import ast

class PlantPredictionView(views.APIView):
    def post(self, request):

        def string_to_array(string):
            array = ast.literal_eval(string)
            return array
        
        def getSuggestions(prediction):
            load_dotenv()
            API_KEY = os.environ.get("API_KEY")
            openai.api_key =API_KEY
            
            content_variable = f"give me some generale suggestion for treating apple scab {prediction}.the response should be in this format: ['suggestion1','suggestion2' ...].The response should be in one line "

            completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": content_variable}
            ]
            )

            return completion.choices[0].message.content
            

        def load_image_from_url(img_url):
            # Create an instance of the urllib3 PoolManager
            http = urllib3.PoolManager()

            # Send a GET request to retrieve the image data
            response = http.request('GET', img_url)
            image_data = response.data

            # Open the image using PIL
            pil_image = Image.open(io.BytesIO(image_data))

            # Resize the image to the target size
            pil_image = pil_image.resize((64, 64))

            # Convert PIL image to Keras image
            img_array = img_to_array(pil_image)

            return np.expand_dims(img_array, axis=0)
        
        model = load_model('./plant_disease.h5')
        
        img_url = request.data['img_url']

        img_array=load_image_from_url(img_url)

        result = {
            0 : 'Strawberry: Leaf_scorch',
            1 : 'Tomato: Tomato_Yellow_Leaf_Curl_Virus',
            2 : 'Tomato: Target_Spot',
            3 : 'Tomato: Late_blight',
            4 : 'Tomato: Spider_mites Two-spotted_spider_mite',
            5 : 'Tomato: Leaf_Mold',
            6 : 'Strawberry: healthy',
            7 : 'Apple: Cedar_apple_rust',
            8 : 'Apple: Black_rot',
            9 : 'Apple: Apple_scab	',
            10 : 'Potato: Late_blight',
            11 : 'Tomato: healthy',
            12 : 'Tomato: Early_blight',
            13 : 'Tomato: Tomato_mosaic_virus',
            14 : 'Tomato: Septoria_leaf_spot',
            15 : 'Potato: Early_blight',
            16 : 'Potato: healthy',
            17 : 'Tomato: Bacterial_spot',
            18 : 'Apple: healthy'
        }

        img_array /= 255

        # Use the model to predict the class of the image
        prediction = model.predict(img_array)
        suggestions=getSuggestions(prediction)
        suggestions=string_to_array(suggestions)

        data= [{"prediction": result[np.argmax(prediction)],'suggestions':suggestions}]
        print(data)
        results = PlantPredictionSerializer(data, many=True).data
        return Response(results)