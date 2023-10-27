import json
from typing import Union
from BilanciaATOMICA import balance_and_rebuild, balance_molar, balance_mass
from fastapi import FastAPI, Response

app = FastAPI()

def load_file_str(name):
    with open(name, "r") as f:
        return f.read()

#read style.css into a variable
style = load_file_str("./sito/style.css")
#read index.html into a variable
index = load_file_str("./sito/index.html")

@app.get("/style.css")
def read_style():
    return Response(content=style, media_type="text/css")

@app.post("/balance_reaction")
def balance_reaction(reaction: str, password: str):
    log = []
    #join log
    try:
        balanced = balance_and_rebuild(reaction, log)
        return {
            "ok": True,
            "reaction": balanced,
            "log": "".join(log)
        }
    except Exception as e:
        #check if e is value error
        if isinstance(e, ValueError):
            log.append("Operazione fallita: " + str(e))
        else:
            print(e)
            log.append("Operazione fallita.")
        
        return {
            "ok": False,
            "reaction": None,
            "log": "".join(log)
        }

@app.get("/balance_molar")
def Abalance_molar(reaction: str, index: int, afterArrow: bool, amount: float):
    log = []
    try:
        balanced = balance_molar(reaction, index, afterArrow, amount)
        return {
            "ok": True,
            "reaction": balanced,
            "log": "".join(log)
        }
    except Exception as e:
        #check if e is value error
        if isinstance(e, ValueError):
            log.append("Operazione fallita: " + str(e))
        else:
            print(e)
            log.append("Operazione fallita.")
        
        return {
            "ok": False,
            "reaction": None,
            "log": "".join(log)
        }

@app.get("/balance_mass")
def Abalance_mass(reaction: str, index: int, afterArrow: bool, amount: float):
    log = []
    try:
        balanced = balance_mass(reaction, index, afterArrow, amount)
        return {
            "ok": True,
            "reaction": balanced,
            "log": "".join(log)
        }
    except Exception as e:
        #check if e is value error
        if isinstance(e, ValueError):
            log.append("Operazione fallita: " + str(e))
        else:
            print(e)
            log.append("Operazione fallita.")
        
        return {
            "ok": False,
            "reaction": None,
            "log": "".join(log)
        }

@app.get("/")
def read_root(reaction: str = ""):
    global index
    result = ""
    log = []
    if reaction != "":
        try:
            balanced = balance_and_rebuild(reaction, log)
            result = balanced
        except Exception as e:
            #check if e is value error
            if isinstance(e, ValueError):
                result = ("Operazione fallita :<br> " + str(e))
            else:
                print(e)
                result = ("Operazione fallita.")
    log = "".join(log)

    bilanci_extra_template = """
    Bilancio molare<br><br>
    Moli (mol)
        <p class="cccwrapper kasokd">%m</p>
    Peso (g)
        <p class="cccwrapper kasokd">%w</p>
    """
    bilanci_extra = ""
    hm = ""
    hw = ""
    _index = 0
    _index1 = 0
    if result and not result.startswith("Operazione fallita"):
        _result = result.split("->")
        for left in _result[0].split("+"):
            _index += 1
            hm += f" <input id=\"Lmindexblm{_index}\" type=\"text\" class=\"mas\"> "
        hm += " -&gt; "
        for right in _result[1].split("+"):
            _index1 += 1
            hm += f"<input id=\"Rmindexblm{_index1}\" type=\"text\" class=\"mas\"> "
        _index = 0
        _index1 = 0
        for left in _result[0].split("+"):
            _index += 1
            hw += f"<input id=\"Lmindexblw{_index}\" type=\"text\" class=\"mas\"> "
        hw += " -&gt; "
        for right in _result[1].split("+"):
            _index1 += 1
            hw += f"<input id=\"Rmindexblw{_index1}\" type=\"text\" class=\"mas\"> "
        bilanci_extra = bilanci_extra_template.replace("%m", hm).replace("%w", hw)
    #convert \n to <br>
    log = log.replace("per il computer", "dal server")
    log = log.replace("```json\n", "<code style=\"font-size: 80%;\">")
    log = log.replace("```\n", "</code>")
    log = log.replace("\n", "<br>")
    gindex = index.replace("%s", result)
    gindex = gindex.replace("%f", log)
    gindex = gindex.replace("%b", bilanci_extra)
    gindex = gindex.replace("%q", json.dumps(result))
    return Response(content=gindex, media_type="text/html")
