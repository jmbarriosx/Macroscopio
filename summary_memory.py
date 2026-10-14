##############################
# Agente Economico De IA     #
# Memoria persistente con    #
# resumen acumulativo        #
##############################

import json
import os
from datetime import datetime


class PersistentMemory:
    """
    Memoria "infinita" en la practica, con 3 capas:

    1. full_log : TODOS los mensajes se guardan en disco (JSON) y nunca se borran.
    2. summary  : resumen acumulado de lo que ya salio de la ventana reciente.
    3. recent   : ultimos mensajes completos; es lo unico (junto al resumen)
                  que se manda al modelo, para no pasar el limite de tokens.

    Cuando recent supera recent_limit, los mensajes mas viejos se resumen
    (el modelo los fusiona con el resumen anterior) y salen de recent.
    """

    def __init__(
        self,
        client,
        filepath: str = "memoria_agente.json",
        recent_limit: int = 10,
        keep_after_summary: int = 4,
        model: str = "openai/gpt-oss-120b",
    ):
        self.client = client
        self.filepath = filepath
        self.recent_limit = recent_limit
        self.keep_after_summary = keep_after_summary
        self.model = model

        self.summary = ""
        self.recent = []
        self.full_log = []

        self._load()

    # ------------------------------------------------------------------
    # Persistencia en disco
    # ------------------------------------------------------------------
    def _load(self):
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.summary = data.get("summary", "")
            self.recent = data.get("recent", [])
            self.full_log = data.get("full_log", [])
        except Exception as e:
            print(f"[PersistentMemory] No se pudo leer {self.filepath}: {e}")

    def _save(self):
        data = {
            "summary": self.summary,
            "recent": self.recent,
            "full_log": self.full_log,
        }
        tmp_path = self.filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.filepath)
        except Exception as e:
            print(f"[PersistentMemory] No se pudo guardar {self.filepath}: {e}")

    # ------------------------------------------------------------------
    # API publica (misma idea que BasicMemory: add / messages)
    # ------------------------------------------------------------------
    def add(self, role: str, text: str):
        self.recent.append({"role": role, "content": text})
        self.full_log.append({
            "role": role,
            "content": text,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })

        if len(self.recent) > self.recent_limit:
            self._compress()

        self._save()

    def messages(self):
        """Mensajes recientes (sin resumen). El resumen se pide aparte con summary."""
        return list(self.recent)

    def clear(self):
        self.summary = ""
        self.recent = []
        self.full_log = []
        try:
            if os.path.exists(self.filepath):
                os.remove(self.filepath)
        except Exception as e:
            print(f"[PersistentMemory] No se pudo borrar {self.filepath}: {e}")

    def stats(self):
        return {
            "total_mensajes": len(self.full_log),
            "mensajes_recientes": len(self.recent),
            "tiene_resumen": bool(self.summary),
        }

    # ------------------------------------------------------------------
    # Compresion: resumir lo viejo
    # ------------------------------------------------------------------
    def _compress(self):
        a_resumir = self.recent[:-self.keep_after_summary]
        if not a_resumir:
            return

        try:
            self.summary = self._summarize(a_resumir)
            self.recent = self.recent[-self.keep_after_summary:]
        except Exception as e:
            # Si falla (por ejemplo rate limit), no perdemos nada: se reintenta
            # en el siguiente mensaje. Tope de seguridad para que recent no crezca sin fin.
            print(f"[PersistentMemory] No se pudo resumir ahora: {e}")
            tope = self.recent_limit * 3
            if len(self.recent) > tope:
                self.recent = self.recent[-tope:]

    def _summarize(self, mensajes):
        lineas = []
        for m in mensajes:
            quien = "Usuario" if m["role"] == "user" else "Agente"
            lineas.append(f"{quien}: {m['content'][:1500]}")
        conversacion = "\n".join(lineas)

        resumen_previo = self.summary if self.summary else "(ninguno todavía)"

        prompt = (
            "Eres un módulo de memoria de un agente económico. Actualiza el resumen "
            "de la conversación fusionando el RESUMEN PREVIO con los MENSAJES NUEVOS.\n"
            "Reglas:\n"
            "- Escribe en español, máximo 150 palabras.\n"
            "- Conserva datos concretos: países, tickers, monedas, años consultados, "
            "cifras importantes, conclusiones y preferencias del usuario.\n"
            "- No inventes nada que no esté en el texto.\n\n"
            f"RESUMEN PREVIO:\n{resumen_previo}\n\n"
            f"MENSAJES NUEVOS:\n{conversacion}\n\n"
            "Devuelve únicamente el resumen actualizado."
        )

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = (resp.choices[0].message.content or "").strip()
        if not texto:
            raise ValueError("El modelo devolvió un resumen vacío")
        return texto
