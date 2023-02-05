import os
from time import sleep

import requests

import logger

log = logger.get_logger(__name__)


class AssemblyAI:
    def __init__(self, api_key, transcript_endpoint, upload_endpoint) -> None:
        log.debug(f'Инициализируем {__name__}')
        self.api_key = api_key
        self.transcript_endpoint = transcript_endpoint
        self.upload_endpoint = upload_endpoint
        self.status = ''

    def read_audio_file(self):
        """Метод-помощник, считывающий аудиофайлы."""
        with open(self.audio_file, 'rb') as f:
            while True:
                data = f.read(5242880)
                if not data:
                    break
                yield data

    def transcript(self, audio_file):
        """Аудио в текст.

        Args:
            audio_file (str): Путь до аудиофайла

        Returns:
            str: возвращает текст
        """
        self.audio_file = audio_file
        headers = {
            'authorization': self.api_key,
            'content-type': 'application/json'
        }
        res_upload = requests.post(
            self.upload_endpoint,
            headers=headers,
            data=self.read_audio_file()
        )
        upload_url = res_upload.json()['upload_url']

        res_transcript = requests.post(
            self.transcript_endpoint,
            headers=headers,
            json={'audio_url': upload_url},
        )
        res_transcript_json = res_transcript.json()
        while self.status != 'completed':
            res_result = requests.get(
                os.path.join(self.transcript_endpoint,
                             res_transcript_json['id']),
                headers=headers
            )
            self.status = res_result.json()['status']
            log.debug(f'Status: { self.status}')

            if self.status == 'error':
                log.error('Аудио файл не удалось обработать.')
                return
            elif self.status != 'completed':
                sleep(10)
        log.info('Аудиофайл обработан успешно!')
        log.info(f"Текст: {res_result.json()['text']}")
        return res_result.json()['text']
