import requests
import json
from datetime import datetime

## config
API_KEY = ''
SYSTEM_ID = ''
DATA_SRC = 'telemetry.json'
STATE_FILE = 'state.json'

class pvoutput:
    def __init__(self) -> None:
        '''
        Assign variables to class instance
        '''
        self.API_KEY = API_KEY
        self.SYSTEM_ID = SYSTEM_ID
        self.DATA_SRC = DATA_SRC
        self.STATE_FILE = STATE_FILE
        self.total_power: int = 0

    def load_state(self) -> json:
        '''
        Load state json file
        '''
        try:
            with open(STATE_FILE, 'r') as file:
                try:
                    return json.load(file)
                except json.decoder.JSONDecodeError:
                    return {}
        except FileNotFoundError:
            self.save_state({})
            return {}
        

    def save_state(self, data) -> None:
        '''
        Save state json to file
        '''
        with open(STATE_FILE, 'w') as file:
            json.dump(data, file, indent=4)
            file.close()

    def update_state(self) -> dict:
        '''
        Update the state with data from telemetry file

        Return: the new state in full if state has changed, otherwise returns False
        '''
        state = self.load_state()
        telemetry = self.load_data()
        data = {**state, **telemetry}
        
        self.save_state(data)
        
        return data

    def load_data(self) -> dict:
        '''
        Load telemetry json file
        '''
        with open(DATA_SRC, 'r') as file:
            return json.load(file)

    def aggregate_data(self, data: json) -> dict:
        '''
        Return: aggregate data for PVOutput
        '''
        avg_temp: int = 0
        avg_volt: int = 0

        for inverter in data:
            self.total_power += data[inverter]['lifetime_wh']
            avg_temp += data[inverter]['temp']
            avg_volt += data[inverter]['ac_volt']

        avg_temp = round((avg_temp / len(data)), 1)
        avg_volt = round((avg_volt / len(data)), 1)

        data = {
            'd': datetime.now().strftime("%Y%m%d"),
            't': datetime.now().strftime("%H:%M"),
            'c1': 2,
            'v1': self.total_power,
            'v5': avg_temp,
            'v6': avg_volt
        }

        return json.dumps(data)

    def upload(self, data) -> str:
        '''
        Upload the data to PVOutput API
        '''
        url = 'https://pvoutput.org/service/r2/addstatus.jsp'
        headers = {
            'X-Pvoutput-Apikey': self.API_KEY,
            'X-Pvoutput-SystemId': self.SYSTEM_ID
        }

        response = requests.post(url, headers=headers, data=json.loads(data))

        return response


if __name__ == '__main__':

    app = pvoutput()

    data = app.update_state()

    pvo_data = app.aggregate_data(data)

    response: requests.Response = app.upload(pvo_data)

    print('HTTP Response:', response.status_code, response.content, sep='\n')