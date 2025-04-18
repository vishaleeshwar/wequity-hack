from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import sys
import time
import webbrowser
import os
import pyautogui
import pyttsx3
import speech_recognition as sr
import pywhatkit
import psutil
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import search_tool, wiki_tool, save_tool
import json
import re
import textwrap
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)
# Initialize the text-to-speech engine
def initialize_engine():
    engine = pyttsx3.init("sapi5")
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)
    volume = engine.getProperty('volume')
    engine.setProperty('volume', volume + 0.25)
    return engine

def speak(text):
    engine = initialize_engine()
    engine.say(text)
    engine.runAndWait()

def command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening...", end="", flush=True)
        r.pause_threshold = 1.0
        r.phrase_threshold = 0.3
        r.sample_rate = 48000
        r.dynamic_energy_threshold = True
        r.operation_timeout = 5
        r.non_speaking_duration = 0.5
        r.dynamic_energy_adjustment = 2
        r.energy_threshold = 4000
        r.phrase_time_limit = 10
        audio = r.listen(source)
    try:
        print("\r", end="", flush=True)
        print("Recognizing...", end="", flush=True)
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
    except Exception as e:
        print("Say that again")
        return "none"
    return query

# Music functionality (from music.py)
def play_music(query):
    song = query.replace("play", "").strip()
    speak(f"Playing {song}")
    pywhatkit.playonyt(song)

# Research paper functionality (from main.py)
def create_research_paper(query):
    load_dotenv()

    class ResearchResponse(BaseModel):
        topic: str
        summary: str
        sources: list[str]
        tools_used: list[str]

    llm = ChatOpenAI(model="gpt-3.5-turbo")
    parser = PydanticOutputParser(pydantic_object=ResearchResponse)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a research assistant that will help generate a research paper.
                Answer the user query and use necessary tools. 
                Wrap the output in this format and provide no other text\n{format_instructions}
                """,
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{query}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    tools = [search_tool, wiki_tool, save_tool]
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )

    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    if("on" not in query):
        speak("Please provide the query in the format 'create research paper on [topic]'")
        return "Invalid query format."
    query = query.split("on")[1].strip()
    print("Query:", query)

    raw_response = agent_executor.invoke({"query": query})
    print("Raw Response Type:", type(raw_response))
    print("Raw Response Content:", )

    

    # Extract topic and summary
    data = json.loads(raw_response['output'])
    topic = sanitize_filename(data.get("topic", "research_paper"))
    summary = data.get("summary", "")
    wrapped_summary = textwrap.fill(summary, width=100)

    # Optional: Add timestamp to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{topic}_{timestamp}.txt"

    # Save to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(wrapped_summary)
    speak(f"The research paper has been created and saved on your desktop as {filename}.")

    # try:
    #     structured_response = parser.parse(raw_response.get("output")[0]["text"])
    #     print("Research Paper Created:")
    #     print(structured_response)

    #     # Save the research paper to a file on the desktop
    #     desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    #     file_path = os.path.join(desktop_path, "research_paper.txt")
    #     with open(file_path, "w") as file:
    #         file.write(str(structured_response))

    #     speak(f"The research paper has been created and saved on your desktop as 'research_paper.txt'.")
    #     raise "Research paper created successfully."
    # except Exception as e:
    #     print("Error parsing response", e, "Raw Response - ", raw_response)
    #     return "Error creating research paper."

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


# Function to answer questions based on the research paper
def answer_questions():
    try:
        # Load the research paper from the saved file
        with open("research_paper.txt", "r") as file:
            research_paper = file.read()

        question =input("what is your question? ")
        llm = ChatOpenAI(model="gpt-3.5-turbo")
        prompt = f"""
        The following is a research paper:
        {research_paper}

        Based on the research paper, answer the following question:
        {question}
        """
        response = llm(prompt)
        print(f"Answer: {response}")
        return response
    except FileNotFoundError:
        return "No research paper found. Please create a research paper first."
    except Exception as e:
        print("Error answering question:", e)
        return "Error answering the question."

def cal_day():
    day=datetime.datetime.today().weekday()+1
    day_dict={
        1:"Monday",
        2:"Tuesday",
        3:"Wednesday",
        4:"Thursday",
        5:"Friday",
        6:"Saturday",
        7:"Sunday"
    }
    if day in day_dict.keys():
        day_of_week=day_dict[day]
        print(day_of_week)
    return day_of_week

def wishme():
    hour=int(datetime.datetime.now().hour)
    t=time.strftime("%I:%M:%p")
    day=cal_day()
    if(hour>=0) and (hour<=12) and ('AM' in t):
        speak(f"Good morning ,it's {day} and the time is {t}")
    elif(hour>=12) and (hour<=16) and ('PM' in t):
        speak(f"Good afternoon ,it's {day} and the time is {t}")
    else:
        speak(f"Good evening ,it's {day} and the time is {t}")

def social_media(command):
    if 'open facebook' in command:
        speak("opening your facebook")
        webbrowser.open("https://www.facebook.com/")
    elif 'open instagram'in command:
        speak("opening your instagram")
        webbrowser.open("https://www.instagram.com/")
    elif 'open discord' in command:
        speak("opening your discord")
        webbrowser.open("https://discord.com/")
    elif 'open whatsapp' in command:
        speak("opening your whatsapp")
        webbrowser.open("https://web.whatsapp.com/")
    elif 'open youtube' in command:
        speak("opening your youtube")
        webbrowser.open("https://www.youtube.com/")
    else:
        speak("no data")

def close_social(command):
    if 'close facebook' in command:
        speak("closing your facebook")
        pyautogui.hotkey('ctrl', 'w')
    elif 'close instagram'in command:
        speak("closing your instagram")
        pyautogui.hotkey('ctrl', 'w')
    elif 'close discord' in command:
        speak("closing your discord")
        pyautogui.hotkey('ctrl', 'w')
    elif 'close whatsapp' in command:
        speak("closing your whatsapp")
        pyautogui.hotkey('ctrl', 'w')
    elif 'close youtube' in command:
        speak("closing your youtube")
        pyautogui.hotkey('ctrl', 'w')

def schedule():
    day= cal_day().lower()
    speak("your today's schedule is")
    week={
    "monday":"from 8:00 am to 9:40 am you have statistics for engineers lab class , from 9:50 am to 11:30 am you have problem solving in oops lab class , from 11:40 am to 1:20 pm you have engneering chemistry lab class ,then you have 1 hour 40 minutes break, after that from 3:00 pm to 3:50 pm you have engneering chemistry theory class , from 4:00 pm to 4:50 pm you have soft skills class, from 5:00 pm to 5:50 pm you have data structure theory class, then finally from 6:00 pm to 6:50 pm you have statistics for engineers theory class.",
    "tuesday":"from 11:40 am to 1:20 pm you have technical english class , then 40 minutes lunch break , after that from 2:00 pm to 2:50 pm you have data structure theory class, from 3:00 pm to 3:50 pm you have statistics for engineers theory class, from 4:00 pm to 4:50 pm you have enivironmental science class, then finally from 5:00 pm to 5:50 pm you have discrete maths class.",
    "wednesday":"from 9:50 am to 11:30 am you have technical english class, then from 2.00 pm to 2:50 pm you have discrete maths class, from 4:00 pm to 4:50 pm you have engineering chemistry theory class, then finally from 5:00 pm to 5:50 pm you have soft skills class.",
    "thursday":"from 8:00 am to 9:40 am you have problem solving in oops lab class, then 2:00 pm to 2:50 pm you have soft skills class, from 3:00 pm to 3:50 pm you have data structure theory class, from 4:00 pm to 4:50 pm you have statistics for engineers theory class, from 5:00 pm to 5:50 pm you have environmental science class ,then finally from 6:00 pm to 6:50 pm you have discrete maths class.",
    "friday":"from 9:50 am to 11:30 am you problem solving in oops class ,from 11:40 am to 1:20 pm you have data structure lab class, from 2:00 pm to 2:50 pm you have environmental science class, from 3:00 pm to 3:50 pm you have discrete maths class, then finally from 5:00 pm to 5:50 pm you have engineering chemistry theory class .",
    "saturday":"it varies for every week.",
    "sunday":"it is holiday,but don't forget to complete your work."
    }
    if day in week.keys():
        speak(week[day])

def openapp(command):
    if "calculator" in command:
        speak("opening calculator")
        os.startfile('c:\\Windows\\system32\\calc.exe')
    elif "notepad" in command:
        speak("opening notepad")
        os.startfile('c:\\Windows\\system32\\notepad.exe')
    elif "this pc" in command:
        speak("opening this pc")
        os.startfile('explorer.exe')

def closeapp(command):
    if "calculator" in command:
        speak("closing calculator")
        pyautogui.hotkey('ctrl', 'w')
    elif "notepad" in command:
        speak("closing notepad")
        os.system('taskkill /f /im notepad.exe')
    elif "this pc" in command:
        speak("closing this pc")
        pyautogui.hotkey('ctrl', 'w')

def browsing(query):
    if 'browser' in query:
        speak("what should i search on browser..") 
        s=command().lower()
        webbrowser.open(f"{s}")

def condition():
    usage =(psutil.cpu_percent())
    speak(f"CPU is at {usage} percentage")
    battery=psutil.sensors_battery()
    percentage=battery.percent
    speak(f"our system have {percentage} percentage battery")

# Flask routes
@app.route('/play', methods=['POST'])
def play():
    data = request.json
    query = data.get('query', '')
    play_music(query)
    return jsonify({"response": f"Playing {query.replace('play', '').strip()} on YouTube."})

@app.route('/answer_question', methods=['POST'])
def answer():
    response = answer_questions()
    return jsonify({"response": response})


def start_talk_ai():
    """
    Start the TalkAi functionality.
    This will run the TalkAi function in a separate thread to avoid blocking the Flask server.
    """
    from threading import Thread
    query = ''
    def run_talk_ai():
        query = startListening()

    thread = Thread(target=run_talk_ai)
    thread.start()
    return jsonify({"response": query})

@app.route('/executequery', methods=['POST'])
def execute_query():
    data = request.json
    query = data.get('query', '')
    query = query.lower()
    if query.startswith("play"):
            play_music(query)
    elif "create research paper" in query:
        speak("Creating a research paper.")
        create_research_paper(query)
    elif "answer question" in query:
        speak("Answering your question based on the research paper.")
        answer_questions()
    elif "exit" in query:
        speak("Bye, it was nice talking to you.")
    else:
    # Execute Jarvis functionality
        if 'open facebook' in query or 'open instagram' in query or 'open discord' in query or 'open whatsapp' in query or 'open youtube' in query:
            social_media(query)
        elif 'close facebook' in query or 'close instagram' in query or 'close discord' in query or 'close whatsapp' in query or 'close youtube' in query:
            close_social(query)
        elif "my schedule" in query:
            schedule()
        elif "volume up" in query or "increase volume" in query:
            pyautogui.press("volumeup")
            speak("Volume increased")
        elif "volume down" in query or "decrease volume" in query:
            pyautogui.press("volumedown")
            speak("Volume decreased")
        elif "volume mute" in query or "mute the volume" in query:
            pyautogui.press("volumemute")
            speak("Volume muted")
        elif "open calculator" in query or "open notepad" in query or "open this pc" in query:
            openapp(query)
        elif "close calculator" in query or "close notepad" in query or "close this pc" in query:
            closeapp(query)
        elif "open browser" in query:
            browsing(query)
        elif "system condition" in query or "condition of the system" in query:
            speak("Checking the system condition")
            condition()
        elif "close" in query:
            speak("Closing")
            pyautogui.hotkey('ctrl', 'w')
    return  jsonify({"response": "query executed successfully."})

@app.route('/start', methods=['GET'])
def startListening():
    speak("How can I help you?")
    return command().lower()


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Backend will run on port 5000