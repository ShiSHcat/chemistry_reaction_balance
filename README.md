# BilanciaATOMICA

### Bilanciatore di reazioni chimiche

Metodo usato: https://www.youtube.com/watch?v=t8-SGrSLUsY \
Supporto al bilanciamento di masse e moli

Creato da [ChristianErba](https://github.com/ChristianErba) e [ShiSHcat](https://github.com/shishcat)

Link: [https://bilancia.shish.cat/](https://bilancia.shish.cat/)


`docker build -t bilancia . && docker run --restart=unless-stopped -it -p 127.0.0.1:9001:9001 bilancia`

Per esecuzione server/background:

`docker run --restart=unless-stopped -itd -p 127.0.0.1:9001:9001 bilancia`
