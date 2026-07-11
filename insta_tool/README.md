# Téléchargeur de Reels Instagram + modification de vitesse

Télécharge des reels Instagram en haute qualité, puis les **accélère ou ralentit
très légèrement de façon aléatoire (±1 à 3 %)** pour désynchroniser l'empreinte
de chaque vidéo.

---

## Installation & lancement sur Mac (3 étapes)

### 1. Ouvre le Terminal
`Cmd + Espace` → tape `Terminal` → Entrée.

### 2. Place-toi dans le dossier
Si tu as cloné le dépôt :
```bash
cd ~/Bobby_prospection_B2B/insta_tool
```

### 3. Lance
```bash
chmod +x run.sh      # une seule fois
./run.sh
```

C'est tout. Au premier lancement, le script installe automatiquement tout ce
qu'il faut (yt-dlp, ffmpeg) dans un environnement isolé. Les vidéos finales
arrivent dans le sous-dossier **`videos/`**.

---

## Choisir les vidéos à télécharger

Ouvre le fichier **`urls.txt`** et colle une URL de reel par ligne :

```
https://www.instagram.com/reel/XXXXXXXXX/
https://www.instagram.com/reel/YYYYYYYYY/
```

Puis relance `./run.sh`.

Tu peux aussi passer les URLs directement :
```bash
./run.sh "https://www.instagram.com/reel/XXXXXXXXX/"
```

---

## Options

| Commande | Effet |
|---|---|
| `./run.sh` | Télécharge tout ce qui est dans `urls.txt` |
| `./run.sh --browser safari` | Utilise tes cookies Safari (débloque les reels récalcitrants) |
| `./run.sh --min 0.95 --max 1.05` | Change l'amplitude de vitesse (ici ±5 %) |
| `./run.sh --no-tweak` | Télécharge sans modifier la vitesse |

---

## Si une vidéo échoue

Instagram bloque parfois l'accès anonyme. Le message le plus fiable pour
débloquer, c'est d'utiliser les cookies de ton navigateur (tu dois être
connecté à Instagram dans ce navigateur) :

```bash
./run.sh --browser safari
```
(remplace `safari` par `chrome` ou `firefox` selon ton navigateur)

Sur macOS avec Safari, autorise l'accès au disque : *Réglages Système →
Confidentialité et sécurité → Accès complet au disque → ajoute Terminal*.

---

## Comment ça marche

1. **Téléchargement** : essaie d'abord `yt-dlp` (meilleure qualité), et bascule
   automatiquement sur la lecture de la page d'intégration (embed) d'Instagram
   si yt-dlp est bloqué — les deux sans cookies pour le contenu public.
2. **Modification** : `ffmpeg` applique un facteur de vitesse aléatoire entre
   0,97× et 1,03× (jamais exactement 1,0), vidéo et audio synchronisés, puis
   réencode en H.264 CRF 18 (qualité quasi identique à l'original).
