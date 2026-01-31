# main flask app file for web-based team communication platform
# based on Leavitt 1949/Bavelas 1950 experiment and including LLMs
# 
# HISTORY
#    - 1/23/25 mbod initial setup (using https://thepythoncode.com/article/how-to-build-a-chat-app-in-python-using-flask-and-flasksocketio)
#
#


from flask import Flask, request, render_template, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send
from network.config import NETWORKS, NODES
from network.node import Node
from typing import Dict, List, Set, Tuple, Optional, Literal, Type
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

import random
import networkx as nx

app = Flask(__name__)
app.config["SECRET_KEY"] = "amIaLLM?"
socketio = SocketIO(app)

# simple datastructure for teams
# TODO: migrate to a database
teams = [
    {
        'name': 'Test1',
        'structure': 'chain',
        'network': NETWORKS['chain'],

        'trial_data': {
              'common_symbol': '&',
              'A': ['#', '&', '$', '@', '%'],
              'B': ['!', '%', '$', '#', '&'],
              'C': ['@', '!', '%', '$', '&'],
              'D': ['!', '&', '%', '#', '@'],
              'E': ['&', '@', '!', '$', '#']
        }
    },

    {
        'name': 'Test2',
        'structure': 'wheel',
        'network': NETWORKS['wheel'],
        
        'trial_data': {
            'common_symbol': '!',
            'A': ['#', '%', '!', '&', '@'],
            'B': ['$', '#', '%', '&', '!'],
            'C': ['#', '!', '@', '$', '%'],
            'D': ['%', '@', '&', '!', '$'],
            'E': ['&', '#', '$', '@', '%']
        }

    }
        
]


# FUNCTIONS

def generate_trial(symbols: List[str],
                   nodes: List[str]):
    '''
    Generate trial data for N nodes from a list of S>N (usually N+1) symbols.
    Constraints: only one symbol from list occurs in ALL node data

    Returns:
        common_symbol: str
        trial_data: Dict[str, List[str]]
    '''

    common_symbol = random.choice(symbols)
    others = [sym for sym in symbols if sym!=common_symbol]
    random.shuffle(others)
    trial_data = {'common_symbol': common_symbol}
    for node, missing in zip(nodes, others):
        trial_data[node] = [sym for sym in symbols if sym!=missing]
        random.shuffle(trial_data[node])

    
    return trial_data




def create_team(name, structure, is_LLM):

    team_data = {
        'name': name,
        'structure': structure,
        'network': NETWORKS[structure],
        'trial_data': generate_trial(["@", "#", "$", "%", "&", "!"], NODES)
    }

    team_data['nodes'] = {node:Node(id=node, 
                                    is_LLM=False if node not in is_LLM else True,
                                    network=team_data['structure'], 
                                    card = ' '.join(team_data['trial_data'][node]))
                                    for node in team_data['network'] 
                         }

    team_network = nx.from_dict_of_lists(team_data['network'])


    plt.figure(figsize=(6,3))
    pos = nx.spring_layout(team_network) 
    nx.draw_networkx(team_network,pos, node_color='lightblue')
    nx.draw_networkx_nodes(team_network, pos, nodelist=is_LLM, node_color='lightgreen')

    human = mpatches.Patch(color='lightblue', label='Human')
    
    llm = mpatches.Patch(color='lightgreen', label='LLM')
    plt.legend(handles=[human,llm])
    
    plt.axis("off")
    plt.savefig(f'static/teams/{name}.png')

    
    return team_data
    

# ROUTES
@app.route('/', methods=["GET","POST"])
def home():
    session.clear()

    team_names = [team['name'] for team in teams]

    
    if request.method == 'POST':
        team_name = request.form.get('team', False)
        member = request.form.get('member', False)
        join = request.form.get('join', False)


        team_data = [team for team in teams if team['name']==team_name]

        if not team_data:
            return render_template('home.html', error="Team is required", team_names=team_names)

        team_data = team_data[0]

        
        if member not in team_data['network'].keys():
            return render_template('home.html', error="Member of team is required", team_names=team_names)
        

        session['team'] = team_name
        return redirect(url_for('chatroom', member=member))

        
    else:
        return render_template('home.html', team_names=team_names)



# Helper functions
@app.route('/team_members', methods=['GET'])
def get_team_members():
    name = request.args.get('team',None)
    member_template = '<option name="member" value="{}">{}</option>'
    try:
        team_data = [team for team in teams if team['name']==name][0]
        
        member_opts = [member_template.format(member, member) 
                           for member, mnode in team_data['nodes'].items()
                               if not mnode.is_LLM and not mnode.in_chat
                       ]
        return '\n'.join([member_template.format('','-')] + member_opts)
    except:
        return [member_template.format('','-')]



@app.route('/chatroom')
def chatroom():
    team_name = session.get('team')
    member = request.args.get('member')

    print(f'Team_name: {team_name} Member: {member}')
    
    try:
        team_data = [team for team in teams if team['name']==team_name][0]
        neighbors = team_data['network'][member]
        symbols = ' '.join(team_data['trial_data'][member])
        
        return render_template('chatroom.html',
                               team=team_name,
                               member=member, 
                               symbols=symbols,
                               neighbors=neighbors)
    except:
        team_names = [team['name'] for team in teams]

        return render_template('home.html', error="Please select Team and Member again", 
                               team_names=team_names)


@app.route('/create_team', methods=['GET','POST'])
def create_new_team():

    if request.method == 'POST':
        team_name = request.form.get('team', False)
        network_structure = request.form.get('structure', False)
        is_LLM_list = request.form.getlist('is_LLM')


        team_data = create_team(team_name, network_structure, is_LLM_list)

        teams.append(team_data)

        print(team_data)
        
        return f"""
        <h3>Team: {team_name}</h3>
        <img src="static/teams/{team_name}.png"/>
        """
        
    else:
        return render_template('create_team.html', 
                               NODES=NODES,
                               NETWORKS=NETWORKS.keys())

# SOCKET IO HANDLERS

@socketio.on('connect')
def handle_connect():
    team_name = session.get('team')
    
    if team_name is None:
        return
    
    join_room(team_name)

@socketio.on('disconnect')
def handle_disconnect():
    team_name = session.get('team')
    
    leave_room(team_name)


@socketio.on('message')
def handle_message(payload):
    team_name = session.get('team')

    # send message
    sender = payload['from']
    recipient = payload['to']
    message = payload['message']

    team_data = [team for team in teams if team['name']==team_name][0]
    nodes = team_data['nodes']
        
    nodes[sender].send_message(nodes[recipient], message)

    print(team_data)
    
    send(payload, to=team_name)

    if nodes[recipient].is_LLM:
        resp = nodes[recipient].take_turn()
        print('===========\n',resp)
        for message in resp['outgoing_messages']:

            nodes[recipient].send_message(nodes[message['to']], message['content'])

            new_message = {'to': message['to'], 'from': recipient, 'message': message['content']}
            print('WS - ', new_message)

            if nodes[message['to']].is_LLM:
                handle_message(new_message)
            else:
                send(new_message, to=team_name)
    

if __name__ == "__main__":

    socketio.run(app, debug=True)