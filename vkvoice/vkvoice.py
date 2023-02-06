import os
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()


class VoiceApiRequest:
    '''Клас для работы с API.'''

    def __init__(self) -> None:
        self.client_id = os.getenv('VK_CLIENT_ID')
        self.client_secret = os.getenv('VK_CLIENT_SECRET')
        self.token = None
        self.headers = "Content-Type: application/json"
        self.auth_endpoint = os.getenv('VK_AUTH_ENDPOINT')
        self.asr_endpoint = os.getenv('ASR_ENDPOINT')

    def get_token(self):
        """Получение токена/авторизация."""
        request_params = {
            'url': self.auth_endpoint,
            'data': {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }
        }

        response = requests.post(**request_params)
        print(response)
        if response.status_code == HTTPStatus.OK:
            self.token = response.json()['access_token']
            # self.token = response.json()['refresh_token']

    def mp3_to_wav(path_to_mp3):
        file = AudioSegment.from_mp3(path_to_mp3)
        path_to_wav = f'{path_to_mp3.spilt(".")[0]}.wav'
        file.export(path_to_wav, format='wav')
        return path_to_wav

    def recognize(self, file_path):
        url = self.asr_endpoint
        file_data = open(file_path, "rb")
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "audio/wave"
            }
            response = requests.post(url, headers=headers, files={
                "file_name": file_data})
        finally:
            file_data.close()
        if response.status_code == HTTPStatus.OK:
            return response.json()['result']['texts']
        else:
            print(response)

    def get_request(self, request_line):
        """GET Запрос до API"""
        request_params = {
            'url': self.endpoint+request_line,
            'headers': self.headers,
        }
        return requests.get(**request_params)

    def post_request(self, request_line: str, data):
        """POST Запрос до API"""
        request_params = {
            'url': self.endpoint+request_line,
            'headers': self.headers,
            'json': data
        }
        return requests.post(**request_params)


voice = VoiceApiRequest()
voice.get_token()
print(voice.token)

print(voice.recognize("audio.wav"))
