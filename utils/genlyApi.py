import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class PreferenceCommand:
    def __init__(self, command, capabilityCategory, providersToUse):
        self.command = command
        self.capabilityCategory = capabilityCategory
        self.providersToUse = providersToUse

    def toDict(self):
        return {
            "command": self.command,
            "capabilityCategory": self.capabilityCategory,
            "providersToUse": self.providersToUse
        }

class GenlyApi:
    def __init__(self, url):
        self.url = url
        self.headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json',
        }
    def generateProviderRecommendations(self, commands: list[str]):
        data = {
            "commands": commands
        }
        response = requests.post(self.url+"/generate-provider-recommendations", headers=self.headers, data=json.dumps(data))
        return response.json()
    
    def generatePreferredTaskSummary(self, preferenceCommands: list[PreferenceCommand]):
        prefs = [pref.toDict() for pref in preferenceCommands]
        data = {
            "channelID": os.getenv("GENLY_API_STREAMLIT_CHANNELID"),
            "preferences": prefs
        }
        response = requests.post(self.url+"/process-preferred-task-summary", headers=self.headers, data=json.dumps(data))
        return response.text
    
    
    def generateMoon(self):
        headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json',
        }
        response = requests.post("https://api.spacexdata.com/v4/rockets/?destination=moon", headers=headers)
        print(response.json())
        return response.json()

if __name__ == "__main__":
    
    url = os.getenv("GENLY_API_URL")
    genlyApi = GenlyApi(url)
    # res = genlyApi.generateMoon()
    # commands = ["Add new contacts to my CRM system",]
    # print(genlyApi.generateProviderRecommendations(commands))

    prefCmd1 = PreferenceCommand("Add new contacts to my CRM system", "CRM", ["Salesforce", "HubSpot"])
    prefCmd2 = PreferenceCommand("Add new songs to my playlist", "Entertainment", ["Spotify", "Youtube"])
    print(genlyApi.generatePreferredTaskSummary([prefCmd1, prefCmd2]))

