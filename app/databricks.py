import os

from databricks.sdk.core import Config
from databricks.connect import DatabricksSession
from databricks.connect.session import DatabricksSession as SparkSession


class SparkConnect():
    """connect to a databricks cluster"""

    workspace_host = os.getenv("DATABRICKS_WORKSPACE_URL")
    cluster_id = os.getenv("DATABRICKS_CLUSTER")
    token = os.getenv("DATABRICKS_TOKEN")

    config = Config(
        host=workspace_host,
        cluster_id=cluster_id,
        token=token
    )

    session = DatabricksSession.builder.sdkConfig(config).getOrCreate()
    spark = SparkSession.builder.sdkConfig(config).getOrCreate()


    def test_connect(self):
        df = self.session.range(1, 10)
        try:
            df.show()
            return True
        except Exception as e:
            print(f"Failed with {str(e)}")
            return False


