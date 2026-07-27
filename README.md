# Whisper Ditado 2

Ditado local e privado para Linux e Windows. O aplicativo fica na bandeja do
sistema: segure **F8** para falar e solte para transcrever. Uma pequena pílula
perto do cursor mostra gravação, nível do microfone e processamento sem tirar o
foco do editor.

## Experiência

- Pílula discreta com medidor de voz, contador e estado de transcrição.
- Modelos `small` e `medium`; a última escolha fica salva.
- Seleção e teste do microfone pela interface.
- Atalho global configurável entre F6 e F12.
- Inicialização automática com o sistema.
- Clipboard Unicode para manter todos os acentos do português.
- Whisper executado localmente; nenhum áudio é enviado para um servidor.

## Desenvolvimento

No Ubuntu/Debian:

```bash
sudo apt install libportaudio2 wl-clipboard ydotool
systemctl --user enable --now ydotool.service
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements-dev.txt
python ditado.py
```

No Windows 10/11:

```powershell
py -3.13 -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python ditado.py
```

Na primeira execução o modelo `small` é baixado para o cache do usuário. Alterar
para `medium` em Configurações baixa o modelo uma vez e mantém essa escolha nas
próximas execuções.

## CLI e diagnóstico

```bash
python ditado.py --listar-microfones
python ditado.py --diagnostico
python ditado.py --sem-interface --modelo medium
```

Os logs ficam no diretório de dados padrão do sistema (`~/.local/state` no Linux
e `%LOCALAPPDATA%` no Windows).

## Particularidades do Linux

No GNOME/Wayland, confirme o atalho solicitado pelo portal na primeira execução.
O `ydotool` é usado apenas para enviar Ctrl+V ao aplicativo em foco. Se ele não
estiver disponível, a transcrição continua no clipboard e pode ser colada
manualmente.

O X11 usa o listener do `pynput` e não precisa do portal do GNOME.

## Testes

```bash
python -m pytest
python -m ruff check src tests ditado.py atalho_wayland.py
```

## Pacotes

Linux (`.deb` e, com `appimagetool`, AppImage):

```bash
scripts/build_linux.sh
```

Windows (PyInstaller + Inno Setup):

```powershell
scripts\build_windows.ps1
```

Os modelos Whisper não entram nos instaladores e são baixados no primeiro uso.

O pacote Debian gerado fica em `dist/whisper-ditado_2.0.0_amd64.deb` e pode ser
instalado com:

```bash
sudo apt install ./dist/whisper-ditado_2.0.0_amd64.deb
```
