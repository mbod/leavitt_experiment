

import asyncio
import socketio

from openai import OpenAI
import json

from dotenv import load_dotenv
_ = load_dotenv()


MODEL_NAME = "gpt-4o-2024-11-20"

ROOM = "test"
SK = 'coll@bplan!'

class Client:

    SYSTEM_PROMPT = '''
        You are engaged in a conversation task as part of a group of 3 people.
        You are Participant {part_id}
        Each of you have a similar image and your task is to identify
        the differences between your versions.
        
        Take a careful look at the scene in the image below. 
        Pay attention to the components of the image and their shape and color etc.
        Once you have looked at the image your are going to talk with 2 others who
        have both have a version of the image but there are NINE differences 
        between your three images and you have to figure them out together.
    
        IMAGE 
        {image}
    
    '''

    
    def __init__(self,
                 id: str,
                 room: str,
                 image_file: str,
                 ws_url: str):

        self.id = id
        self.room = room




        self.image = open(f'images/{image_file}').read()
        self.prompt = self.SYSTEM_PROMPT.format(part_id=self.id,
                                                image=self.image)

        self.history = []
        
        # websocket url for connection
        self.ws_url = ws_url
        self.sio = socketio.AsyncClient()        

        # LLM object
        self.LLM = OpenAI()

        # register handlers for websocket events
        self.register_handlers()

    def __repr__(self):
        return f"""Client(id='{self.id},
                          room='{self.room},
                          ws_url='{self.ws_url}'
                          prompt='{self.prompt}'

                """

    def register_handlers(self):
        
        @self.sio.event
        async def connect():
    
            print(f"Client {self.id} connected")
            await self.sio.emit("join", {
                "id": self.id,
                "room": "test",
                "kind": "agent"
            })



            '''
            # connect to websocket
            await self.sio.connect(self.ws_url, auth=auth)
    
            # Joining message 
            greeting = {"from": self.id, "message":  f"Hi everyone! I'm {self.id}"}
            await self.sio.emit("message", greeting)
            
            await self.sio.wait()

            '''

        @self.sio.event
        async def disconnect():
            print(f"Client {self.id} disconnected")
            

        @self.sio.on("message")
        async def on_message(message):
            sender = message['from']
            message = message['message']

            message_dict = {"role": "user",
                            "content": f"{sender}: {message}"}
            
            self.history.append(message_dict)

            # don't respond to your own messages
            # ? should this be in the respond function??
            last_speaker = self.history[-1]['content'][:1]
            print(f'Last turn by {last_speaker}')
            if last_speaker != self.id:
                await self.respond()
            else:
                

                
    
    async def respond(self):
        '''
        Look at message history and make your response
        '''
        print('respond')
        try:

            resp = self.take_turn()
            if resp['current_action'].count('wait'):
                new_message = {
                    "from": self.id,
                    "message": "What features do you see in your images?"
                }
            else:
                new_message = {
                    "from": self.id,
                    "message": f"{resp['message']}"
                }
                
            await self.sio.emit("message", new_message)
        finally:
            pass


    def take_turn(self):
        '''
        Evaluate the current state of the group discussion and 
        decide what action to take
        - send a message with information about your image
        - wait for more input from other members of the group
        - make a suggestion of a difference

        '''

        TURN_PROMPT = f'''
                Evaluate the current state of the group discussion and 
                decide what action to take
                - send a message with information about your image
                - wait for more input from other members of the group
                - make a suggestion of a difference

                - Output MUST be valid JSON with keys: 
                    current_action
                    message
        '''

        # set up the messages data structure
        messages = [
            {'role': 'system', 'content': self.prompt }
        ]
        messages.extend(self.history)
        messages.append(
            {'role': 'user', 'content': TURN_PROMPT }
        )


        # call LLM
        response = self.LLM.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            response_format={"type": "json_object"}
        )

        # parse response
        resp = json.loads(response.choices[0].message.content)

        print(resp)
        
        return resp


    async def run(self, auth):
        await self.sio.connect(self.ws_url, auth=auth)
        await self.sio.emit("message", {"from": auth['sid'], "message": f"Hi I'm here!"})
        await self.sio.wait()

def run_agent(agent_id):
    client = Client(agent_id, ROOM, f'image{agent_id}.svg', 'ws://localhost:5555')
    auth = { "room": ROOM, "sid": agent_id, "token": SK}

    asyncio.run(client.run(auth))