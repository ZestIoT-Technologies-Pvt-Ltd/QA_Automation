<<<<<<< HEAD
import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    @staticmethod
    def get_env():
        return os.getenv("ENV", "qa").lower()

    @staticmethod
    def get_url():
        env = Config.get_env()

        urls = {
            "qa": os.getenv("QA_URL"),
            "stage": os.getenv("STAGE_URL"),
            "prod": os.getenv("PROD_URL")
        }

        return urls.get(env)

    @staticmethod
    def get_username():
        env = Config.get_env()

        users = {
            "qa": os.getenv("QA_USERNAME"),
            "stage": os.getenv("STAGE_USERNAME"),
            "prod": os.getenv("PROD_USERNAME")
        }

        return users.get(env)

    @staticmethod
    def get_password():
        env = Config.get_env()

        passwords = {
            "qa": os.getenv("QA_PASSWORD"),
            "stage": os.getenv("STAGE_PASSWORD"),
            "prod": os.getenv("PROD_PASSWORD")
        }

        return passwords.get(env)
=======
import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    @staticmethod
    def get_config(project, env):
        """
        Dynamically fetch configuration
        based on project and environment.
        """

        project = project.upper()
        env = env.upper()

        config = {
            "url": os.getenv(f"{project}_{env}_URL"),
            "username": os.getenv(f"{project}_{env}_USERNAME"),
            "password": os.getenv(f"{project}_{env}_PASSWORD")
        }

        if not config["url"]:
            raise ValueError(
                f"Configuration not found for "
                f"PROJECT={project} ENV={env}"
            )

        return config
>>>>>>> 8d21396 (Update automation framework and test cases)
