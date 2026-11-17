// ============================================================================
// TESTE DA BASE (Heltec) PARA O ABATRACK  -  sem radio, sem OBC
//
// Imprime na serial exatamente o que o lorarx.cpp imprime, mas com valores
// ficticios, para testar a recepcao no AbaTrack:
//
//   - telemetria: 1 linha por segundo, 19 campos separados por ":"
//                 (inclui o angulo LDR na posicao 11, como o AbaTrack espera)
//   - foto:       IMAGE_BEGIN / SIZE:<n> / <n bytes> / IMAGE_END, a cada 15 s
//   - ADS-B:      ORANGE:AC,... seguida de "missão: ..." (so quando ligado)
//
// Comandos (digite na serial, 115200, terminando com Enter; no AbaTrack use o
// campo "Digite o comando serial"):
//   img      envia a foto agora
//   rajada   envia 100 linhas de ADS-B coladas e depois a foto
//            (reproduz o caso em que a foto se perdia no AbaTrack)
//   orange   liga/desliga as linhas de ADS-B periodicas (comeca desligado)
//   auto     liga/desliga a foto automatica a cada 15 s (comeca ligado)
//   stats    mostra o que ja foi enviado
//
// Gravar na Heltec no lugar do lorarx. Arquivos: teste_base.ino e
// imagem_teste.h na mesma pasta (a pasta precisa se chamar teste_base).
// ============================================================================

#include <Arduino.h>
#include "imagem_teste.h"

#define INTERVALO_TELEMETRIA_MS  1000UL
#define INTERVALO_FOTO_MS        15000UL
#define INTERVALO_ORANGE_MS      500UL

static bool     fotoAutomatica = true;
static bool     orangeLigado   = false;

static uint32_t ultimaTelemetria = 0;
static uint32_t ultimaFoto       = 0;
static uint32_t ultimoOrange     = 0;

static uint32_t totalTelemetrias = 0;
static uint32_t totalFotos       = 0;
static uint32_t totalLinhasAC    = 0;
static uint32_t seqAC            = 0;

// Tres aeronaves ficticias
static const char* const ICAO[3] = { "40621D", "7788FF", "E49401" };

// Mesma impressao do finalizarImagem() do lorarx.cpp
static void enviarFoto()
{
    Serial.print("IMAGE_BEGIN\n");
    Serial.printf("SIZE:%lu\n", (unsigned long)IMAGEM_TESTE_TAM);
    Serial.write(IMAGEM_TESTE, IMAGEM_TESTE_TAM);
    Serial.print("IMAGE_END\n");
    totalFotos++;
}

// Mesma ordem do vetor do AbaTrack (19 campos)
static void enviarTelemetria()
{
    float t = millis() / 1000.0f;

    Serial.print((unsigned long)(millis() / 1000)); Serial.print(":");   //  1 tempo (s)
    Serial.print(25.0f + 2.0f * sinf(t / 10.0f), 2); Serial.print(":");  //  2 temperatura
    Serial.print(40.0f + 5.0f * cosf(t / 20.0f), 2); Serial.print(":");  //  3 umidade
    Serial.print(100.0f + 10.0f * t, 1);             Serial.print(":");  //  4 altitude (m)
    Serial.print(101325UL - (unsigned long)(t * 12)); Serial.print(":"); //  5 pressao (Pa)
    Serial.print(-22.9068f + 0.0001f * t, 7);        Serial.print(":");  //  6 latitude
    Serial.print(-43.1729f + 0.0001f * t, 7);        Serial.print(":");  //  7 longitude
    Serial.print(7);                                 Serial.print(":");  //  8 satelites
    Serial.print(10.0f * sinf(t / 5.0f), 2);         Serial.print(":");  //  9 roll
    Serial.print(10.0f * cosf(t / 5.0f), 2);         Serial.print(":");  // 10 pitch
    Serial.print(fmodf(t * 5.0f, 360.0f), 2);        Serial.print(":");  // 11 yaw
    Serial.print(45.0f + 20.0f * sinf(t / 8.0f), 2); Serial.print(":");  // 12 angulo LDR
    Serial.print(30.0f, 2);                          Serial.print(":");  // 13 temp bateria 1
    Serial.print(31.0f, 2);                          Serial.print(":");  // 14 temp bateria 2
    Serial.print(7.4f, 3);                           Serial.print(":");  // 15 tensao (V)
    Serial.print(1.2f, 3);                           Serial.print(":");  // 16 corrente (A)
    Serial.print((unsigned long)(totalTelemetrias + 1)); Serial.print(":"); // 17 numero de pacotes
    Serial.print(-30);                               Serial.print(":");  // 18 RSSI
    Serial.println(41);                                                  // 19 tamanho do pacote
    totalTelemetrias++;
}

// Uma aeronave: linha ORANGE:AC (banco/CSV) + linha "missão:" (mapa)
static void enviarAC(int aviao)
{
    float t = millis() / 1000.0f;
    float lat = -22.90f + 0.02f * aviao + 0.0005f * t;
    float lon = -43.30f + 0.03f * aviao + 0.0007f * t;
    int alt = 30000 + 1500 * aviao;
    int gs  = 420 + 15 * aviao;
    int rumo = 60 + 40 * aviao;
    unsigned long ts = 1790950771UL + (unsigned long)t;

    seqAC++;
    Serial.printf("ORANGE:AC,%lu,%lu.000,%s,%.5f,%.5f,%d,%d,%d\n",
                  (unsigned long)seqAC, ts, ICAO[aviao], lat, lon, alt, gs, rumo);
    Serial.printf("missão: %s, %.5f, %.5f, %d\n", ICAO[aviao], lat, lon, alt);
    totalLinhasAC += 2;
}

static void enviarRajada()
{
    for (int i = 0; i < 100; i++) {
        enviarAC(i % 3);
    }
    enviarFoto();
}

static void mostrarStats()
{
    Serial.println();
    Serial.println("========== TESTE BASE ==========");
    Serial.print("Telemetrias enviadas: "); Serial.println(totalTelemetrias);
    Serial.print("Fotos enviadas      : "); Serial.println(totalFotos);
    Serial.print("Linhas de ADS-B     : "); Serial.println(totalLinhasAC);
    Serial.print("Foto automatica     : "); Serial.println(fotoAutomatica ? "ligada" : "desligada");
    Serial.print("ADS-B periodico     : "); Serial.println(orangeLigado ? "ligado" : "desligado");
    Serial.println("================================");
}

static void tratarComando(String cmd)
{
    cmd.trim();
    cmd.toLowerCase();
    if (cmd.length() == 0) return;

    if (cmd == "img") {
        enviarFoto();
    } else if (cmd == "rajada") {
        enviarRajada();
    } else if (cmd == "orange") {
        orangeLigado = !orangeLigado;
        Serial.print("ADS-B periodico: "); Serial.println(orangeLigado ? "ligado" : "desligado");
    } else if (cmd == "auto") {
        fotoAutomatica = !fotoAutomatica;
        Serial.print("Foto automatica: "); Serial.println(fotoAutomatica ? "ligada" : "desligada");
    } else if (cmd == "stats") {
        mostrarStats();
    } else {
        Serial.print("Comando enviado para OBC: ");   // mesma resposta do lorarx.ino
        Serial.println(cmd);
    }
}

void setup()
{
    Serial.begin(115200);
    Serial.setTimeout(20);
    delay(500);
    ultimaTelemetria = millis();
    ultimaFoto       = millis();
    ultimoOrange     = millis();
}

void loop()
{
    uint32_t agora = millis();

    if (Serial.available()) {
        tratarComando(Serial.readStringUntil('\n'));
    }

    if (agora - ultimaTelemetria >= INTERVALO_TELEMETRIA_MS) {
        ultimaTelemetria = agora;
        enviarTelemetria();
    }

    if (orangeLigado && agora - ultimoOrange >= INTERVALO_ORANGE_MS) {
        ultimoOrange = agora;
        for (int i = 0; i < 3; i++) enviarAC(i);
    }

    if (fotoAutomatica && agora - ultimaFoto >= INTERVALO_FOTO_MS) {
        ultimaFoto = agora;
        enviarFoto();
    }
}
