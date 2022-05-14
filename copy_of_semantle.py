# -*- coding: utf-8 -*-
"""Copy of semantle.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FQP7U1Bo9KbqvqqlPF3BhrgOVj9eMelN
"""

import os
path = '/content/drive/MyDrive/projects/SimLing/semantle/semantle_master'
os.chdir(path)
os.listdir(path)

#!brew install wget

#!wget -c "https://s3.amazonaws.com/dl4j-distribution/GoogleNews-vectors-negative300.bin.gz"

#!gzip -d GoogleNews-vectors-negative300.bin.gz

!pip install aniso8601==9.0.1 click==8.0.3 Flask==2.0.3 Flask-RESTful==0.3.6 future==0.17.1 \
gensim==4.1.2 \
itsdangerous==2.0.1 \
Jinja2==3.0.3 \
joblib==1.1.0 \
MarkupSafe==2.0.1 \
nltk==3.6.7 \
pytz==2021.3 \
regex==2022.1.18 \
scipy==1.7.3 \
six==1.16.0 \
smart-open==5.2.1 \
tqdm==4.62.3 \
Werkzeug==2.0.2 \
black==22.1.0 \
more-itertools \
flask_ngrok \
googletrans==3.1.0a0

#!python semantle.py

!pip install pyngrok==4.1.1
!ngrok authtoken 277nDzi2Ir9gCW1nNDxyRg6Ak1R_7ijhyUWBSYdxQZ9WWDmuj

from flask import (
    Flask,
    request,
    jsonify,
    send_file,
    send_from_directory,
    render_template,
)
import struct
import sqlite3
import base64
from functools import lru_cache
from flask_ngrok import run_with_ngrok
from googletrans import Translator
translator = Translator()

import socket
print(socket.gethostbyname(socket.getfqdn(socket.gethostname())))

app = Flask(__name__)
run_with_ngrok(app)

@app.route("/")
def send_index():
    return send_file("static/index.html")


@app.route("/favicon.ico")
def send_favicon():
    return send_file("static/assets/favicon.ico")


@app.route("/assets/<path:path>")
def send_static(path):
    return send_from_directory("static/assets", path)


def expand_bfloat(vec, half_length=600):
    """
    expand truncated float32 to float32
    """
    if len(vec) == half_length:
        vec = b"".join((b"\00\00" + bytes(pair)) for pair in zip(vec[::2], vec[1::2]))
    return vec


@app.route("/model/<string:word>")
def word(word):
    word = translator.translate(word).text
    try:
        con = sqlite3.connect("word2vec.db")
        cur = con.cursor()
        res = cur.execute("SELECT vec FROM word2vec WHERE word = ?", (word,))
        res = list(cur.fetchone())
        con.close()
        if not res:
            return ""
        res = res[0]
        return jsonify(list(struct.unpack("300f", expand_bfloat(res))))
    except Exception as e:
        print(e)
        return jsonify(e)


@lru_cache(maxsize=50000)
def get_model2(secret, word):
    word = translator.translate(word).text
    con = sqlite3.connect("word2vec.db")
    cur = con.cursor()
    res = cur.execute(
        "SELECT vec, percentile FROM word2vec left outer join nearby on nearby.word=? and nearby.neighbor=? WHERE word2vec.word = ?",
        (secret, word, word),
    )
    row = cur.fetchone()
    if row:
        row = list(row)
    con.close()
    if not row:
        return ""
    vec = row[0]
    result = {"vec": list(struct.unpack("300f", expand_bfloat(vec)))}
    if row[1]:
        result["percentile"] = row[1]
    return jsonify(result)


@app.route("/model2/<string:secret>/<string:word>")
def model2(secret, word):
    word = translator.translate(word).text
    try:
        return get_model2(secret, word)
    except Exception as e:
        print(e)
        return jsonify(e)


@app.route("/similarity/<string:word>")
def similarity(word):
    word = translator.translate(word).text
    try:
        con = sqlite3.connect("word2vec.db")
        cur = con.cursor()
        res = cur.execute(
            "SELECT top, top10, rest FROM similarity_range WHERE word = ?", (word,)
        )
        res = list(cur.fetchone())
        con.close()
        if not res:
            return ""
        return jsonify({"top": res[0], "top10": res[1], "rest": res[2]})
    except Exception as e:
        print(e)
        return jsonify(e)


@app.route("/nearby/<string:word>")
def nearby(word):
    word = translator.translate(word).text
    try:
        con = sqlite3.connect("word2vec.db")
        cur = con.cursor()
        res = cur.execute(
            "SELECT neighbor FROM nearby WHERE word = ? order by percentile desc limit 10 offset 1",
            (word,),
        )
        rows = cur.fetchall()
        con.close()
        if not rows:
            return ""
        return jsonify([row[0] for row in rows])
    except Exception as e:
        print(e)
        return jsonify(e)


@app.route("/nearby_1k/<string:word_b64>")
def nearby_1k(word_b64):
    try:
        word = base64.b64decode(word_b64).decode("utf-8")

        con = sqlite3.connect("word2vec.db")
        cur = con.cursor()
        res = cur.execute(
            "SELECT neighbor, percentile, similarity FROM nearby WHERE word = ? order by percentile desc limit 1000 offset 1 ",
            (word,),
        )
        rows = cur.fetchall()
        con.close()
        words = [
            dict(
                neighbor=row[0],
                percentile=int(row[1]),
                similarity="%0.2f" % (100 * row[2]),
            )
            for row in rows
        ]
        return render_template("top1k.html", word=word, words=words)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return "Oops, error"


@app.errorhandler(404)
def not_found(error):
    return "page not found"


@app.errorhandler(500)
def error_handler(error):
    return error


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    import sqlite3

    app.run()

import IPython.display

def display(port, height):
    shell = """
        (async () => {
            const url = await google.colab.kernel.proxyPort(%PORT%, {"cache": true});
            const iframe = document.createElement('iframe');
            iframe.src = url;
            iframe.setAttribute('width', '100%');
            iframe.setAttribute('height', '%HEIGHT%');
            iframe.setAttribute('frameborder', 0);
            document.body.appendChild(iframe);
        })();
    """
    replacements = [
        ("%PORT%", "%d" % port),
        ("%HEIGHT%", "%d" % height),
    ]
    for (k, v) in replacements:
        shell = shell.replace(k, v)

    script = IPython.display.Javascript(shell)
    IPython.display.display(script)

display(6060, 400)

!pip install flask-ngrok
from flask import Flask
from flask_ngrok import run_with_ngrok
app = Flask(__name__)
run_with_ngrok(app)   
  
@app.route("/")
def home():
    return "<h1>GFG is great platform to learn</h1>"
    
app.run()

'''
import collections.abc

collections.Mapping = collections.abc.Mapping

import gensim.models.keyedvectors as word2vec
import numpy as np

import sqlite3
import tqdm

from more_itertools import chunked

model = word2vec.KeyedVectors.load_word2vec_format(
    "../GoogleNews-vectors-negative300.bin", binary=True
)

con = sqlite3.connect("word2vec.db")
con.execute("PRAGMA journal_mode=WAL")
cur = con.cursor()
cur.execute("""create table if not exists word2vec (word text PRIMARY KEY, vec blob)""")
con.commit()

# import pdb;pdb.set_trace()


def bfloat(vec):
    """
    Half of each floating point vector happens to be zero in the Google model.
    Possibly using truncated float32 = bfloat. Discard to save space.
    """
    vec.dtype = np.int16
    return vec[1::2].tobytes()


# many weird words contain #, _ for multi-word
# some have e-mail addresses, start with numbers, :-), lots of === signs, ...

CHUNK_SIZE = 1111
con.execute("DELETE FROM word2vec")
'''
