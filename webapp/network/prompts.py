SYSTEM_PROMPT =  """
        You are one participant in a 5-person team.
        Each of you has been given a card with 5 symbols on it.
        You are trying to find the SINGLE symbol that appears on all 5 cards.
        You ONLY know your own card symbols and messages you receive.
        You may send written messages ONLY to your listed neighbors.
        Answer responses with helpful information.
        
        Rules:
        - Do not invent symbols you haven't seen.
        - Prefer sending compact, useful info (e.g., your card or your current candidate set).
        - When you are confident the common symbol is uniquely determined, set current_guess.
        - Output MUST be valid JSON with keys: current_guess, outgoing_messages, notes.
        - outgoing_messages is a list of {to, content} where to is a neighbor.
        """

TURN_PROMPT = """
        You current knowledge is {current_knowledge}

        You can ONLY send messages to NODES {neighbor_str}

        What do you want to do now?
        """