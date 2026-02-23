import json
import requests
from urllib.parse import quote
from typing import Any


DOMAIN = "theses.fr"
ENDPOINT = "/api/v1/theses/recherche/"
RESPONSE_DATA = "data-raw.json"
OUTFILE = "data-clean.json"
MAKE_REQUEST = True
KEYWORDS = [
    "Cryptographie",
    "Cryptologie",
    "Cryptanalyse",
    "Attaques par canaux cachés",
    "Bases de Gröbner",
    "Générateurs de nombre pseudo-aléatoires"
]


def build_queryurl(pageindex: int, amount: int, keywords: list[str]) -> str:
    kws = ''.join(
        f"(sujetsLibelle%3A({ kw })%20OR%20sujetsRameauLibelle%3A({ kw })%20OR%20sujetsRameauPpn%3A({ kw }))%20OR%20titres.%5C*%3A({ kw })"
        for kw in map(quote, keywords)
    )

    return "https://" + DOMAIN + ENDPOINT +                 \
        f"?debut={ pageindex * amount }&nombre={ amount }"  \
        f"&tri=pertinence"                                  \
        f"&filtres=%5BStatut%3D%22soutenue%22%5D"           \
        f"&q={ kws }"


if MAKE_REQUEST:
    session = requests.Session()

    all_thesis: list[dict[str, Any]] = [ ]

    response = session.get(build_queryurl(0, 10000, KEYWORDS))

    assert response.status_code == 200

    all_thesis += response.json()["theses"]

    print(f"Total: { len(all_thesis) }.")

    with open(RESPONSE_DATA, "w") as file:
        data = json.dump(all_thesis, file)


with open(RESPONSE_DATA, "r") as file:
    all_thesis = json.load(file)


class Researcher:
    def __init__(self, ppn: str, fname: str, lname: str, thesis_id: str | None = None) -> None:
        self.ppn = ppn
        self.fname = fname
        self.lname = lname
        self.thesis_id = thesis_id
        self.supervisions: set[str] = set()

    def add_thesis(self, thesis_id: str):
        self.thesis_id = thesis_id

    def add_supervision(self, thesis_id: str):
        self.supervisions.add(thesis_id)

    def to_dict(self) -> dict[str, str | list[str] | None]:
        return {
            "ppn": self.ppn,
            "fname": self.fname,
            "lname": self.lname,
            "thesis_id": self.thesis_id,
            "supervisions": list(self.supervisions)
        }


class Thesis:
    def __init__(self, tid: str,  ppn: str, title: str, supervisors: set[str], defense: str) -> None:
        self.tid = tid
        self.ppn = ppn
        self.title = title
        self.supervisors = supervisors
        self.defense = defense

    def to_dict(self) -> dict[str, str | list[str]]:
        return {
            "tid": self.tid,
            "ppn": self.ppn,
            "title": self.title,
            "supervisors": list(self.supervisors),
            "defense": self.defense
        }


thesisdb: dict[str, Thesis] = { }
researchersdb: dict[str, Researcher] = { }

for thesis_data in all_thesis:
    tid: str = thesis_data["id"]

    author = thesis_data["auteurs"][0]
    if author.get("ppn") is None:
        print("Thesis author without a PPN:", author)
        continue

    researcher = researchersdb.get(author["ppn"])
    if researcher is None:
        researcher = Researcher(
            author["ppn"],
            author["prenom"],
            author["nom"]
        )

    researcher.thesis_id = tid

    thesis_supervisors: set[str] = set()
    for superviser_data in thesis_data["directeurs"]:
        supervisor_ppn = superviser_data["ppn"]
        if supervisor_ppn is None:
            print("Invalid superviser", superviser_data)
            continue

        supervisor = researchersdb.get(supervisor_ppn)

        if supervisor is None:
            supervisor = Researcher(supervisor_ppn, superviser_data["prenom"], superviser_data["nom"])
            researchersdb[supervisor.ppn] = supervisor

        supervisor.add_supervision(tid)

        thesis_supervisors.add(supervisor.ppn)

    thesis = Thesis(
        tid,
        author["ppn"],
        thesis_data["titrePrincipal"],
        thesis_supervisors,
        thesis_data["dateSoutenance"]
    )

    thesisdb[tid] = thesis
    researchersdb[author["ppn"]] = researcher


# Preparing data
nodes: list[dict[str, dict[str, str]]] = [ ]
edges: list[dict[str, dict[str, str]]] = [ ]
for researcher in researchersdb.values():
    thesis = None

    if researcher.thesis_id:
        thesis = thesisdb.get(researcher.thesis_id)

    nodes.append({
        "data": {
            "id": researcher.ppn,
            "label": researcher.fname + ' ' + researcher.lname.upper(),
            "info": thesis.title if thesis else '',
            "year": thesis.defense.rsplit('/')[-1] if thesis else ''
        }
    })

    for tid in researcher.supervisions:
        edges.append({ "data": { "source": researcher.ppn, "target": thesisdb[tid].ppn }})

print(len(nodes), "nodes and", len(edges), "edges.")

with open(OUTFILE, "w") as file:
    json.dump({ "nodes": nodes, "edges": edges }, file)

print("Done")
