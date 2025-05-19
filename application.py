from flask import Flask, render_template, request
import logging
import traceback
from pipeline.prediction_pipeline import hybrid_recommendation

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    recommendations = None
    if request.method == 'POST':
        try:
            user_id = int(request.form["userID"])
            logger.info(f"Processing recommendation request for user_id: {user_id}")
            recommendations = hybrid_recommendation(user_id)
            
            if recommendations:
                logger.info(f"Successfully generated recommendations for user_id {user_id}: {recommendations}")
            else:
                logger.warning(f"No recommendations generated for user_id {user_id}")
                
        except ValueError as ve:
            # Handle case where user ID is not a valid integer
            logger.error(f"Invalid user ID format: {request.form.get('userID', 'unknown')}")
            logger.error(f"Error details: {str(ve)}")
            print(f"Error occurred: Invalid user ID format - {str(ve)}")
        except Exception as e:
            # Handle other exceptions
            logger.error(f"Error generating recommendations for user: {request.form.get('userID', 'unknown')}")
            logger.error(f"Error details: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"Error occurred: {str(e)}")
    return render_template('index.html', recommendations=recommendations)

if __name__ == "__main__":
    logger.info("Starting recommendation service")
    app.run(debug=True, host='0.0.0.0', port=5000)
