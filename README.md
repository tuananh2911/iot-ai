# Plant Disease Detection Backend

This repository contains the backend code for PlantDiseaseDetection, a web application built using Django. The backend primarily serves as an API that returns predictions and suggestions for plant disease detection. The predictions are obtained using a pre-trained CNN deep learning model, while the suggestions are generated using the GPT-3 API.

## Endpoint

The backend exposes a single endpoint:

### `/plant_prediction`

This endpoint accepts a POST request and returns a JSON response containing the prediction and suggestions for the provided image.

**Request Parameters:**

- `img_link` (string): The link to the image to be processed.

**Example Request:**

```json
{
  "img_url": "image/url"
}
```

**Example Response:**

```json
{
  "prediction": "Tomato Leaf Mold",
  "suggestions": [
    "Apply appropriate fungicide.",
    "Ensure proper watering to prevent leaf wetness."
  ]
}
```

## Setup

To set up the Plant Disease Detection backend locally, follow the instructions below:

1. Clone the repository:

   ```bash
   git clone https://github.com/mbahraoui/Plant-DiseaseDetection-Backend.git
   ```

2. Navigate to the project directory:

   ```bash
   cd Plant-DiseaseDetection-Backend
   ```

3. Create a `.env` file in PlantPrediction directory of the project and add the following line:

   ```plaintext
   API_KEY=your_api_key
   ```

   Replace `your_api_key` with your actual GPT-3 API key.

4. Start the Django development server:

   ```bash
   python manage.py runserver
   ```

   The backend should now be running at `http://localhost:8000/`.

## Training the Model

The CNN deep learning model used for plant disease detection was trained using Google Colab. The training notebook can be found at the following link:

[Google Colab Training Notebook](https://colab.research.google.com/drive/166xQ-6AybNGNeDIcF3mbh2LI0Y3iFeAc?usp=sharing)

Please refer to the notebook for the detailed training process and steps.
