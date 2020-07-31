import os
import requests
import base64
import time


class ImgurUploader:
    """
    Class to upload images to imgur
    """

    def __init__(self):
        self.clientid = os.environ["IMGURCLIENTID"]
        print(f'uploading anonymously via {self.clientid}')

    def upload(self, image: bytes):
        """
        Upload an image anonymously to imgur

        :rtype: (str, str)
        :param image: byte data for image
        :return: imgur link, deleteHash
        """

        auth_header = {"Authorization": f"Client-ID {self.clientid}"}

        # Check for available upload credits
        limits = requests.get(url='https://api.imgur.com/3/credits',
                              headers=auth_header)
        data = limits.json()['data']
        userRemaining = int(data['UserRemaining'])
        clientRemaining = int(data['ClientRemaining'])
        remainingCredits = min(userRemaining, clientRemaining)
        resetTimestamp = int(data['UserReset'])
        timedelta = resetTimestamp - int(time.time())
        print(f'Remaining Credits : {remainingCredits}\n'
              f'User Credits : {userRemaining}\n'
              f'Client Credits : {clientRemaining}\n'
              f'Reset Time: {resetTimestamp} in {timedelta/60:.2f} mins\n')

        # Check if upload is allowed at this time
        if remainingCredits == 0:
            if userRemaining == 0:
                while resetTimestamp - int(time.time()) > 0:
                    print(f'\nOUT OF IMGUR CREDITS: Waiting for {(resetTimestamp - int(time.time()))/60:.2f} mins')
                    time.sleep(60)
            elif clientRemaining == 0:
                print('IMGUR Client is out of credits. End of upload for the day.')
                raise RuntimeError('IMGUR: Out of Client Credits for the day.')

        # Upload image
        form = {
            'image': base64.b64encode(image),
            'type': 'base64'
        }

        r = requests.post(url='https://api.imgur.com/3/upload',
                          headers=auth_header,
                          data=form)

        link = r.json()['data']['link']
        deleteHash = r.json()['data']['deletehash']

        print(f'Uploaded {link}')

        return link, deleteHash


if __name__ == '__main__':
    img = ImgurUploader()
    with open('2019.png', 'rb') as f:
        img.upload(f.read())
