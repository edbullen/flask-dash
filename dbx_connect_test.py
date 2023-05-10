# Start the Flask application by importing the app package instance
from app.databricks import SparkConnect


if __name__ == '__main__':
    con = SparkConnect()
    status = con.test_connect()
    if status:
        print("Success")
    else:
        print("Failed - check the DATABRICKS_CLUSTER, DATABRICKS_WORKSPACE_URL, DATABRICKS_TOKEN environment variables")
