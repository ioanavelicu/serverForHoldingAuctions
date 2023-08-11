import socket
import threading
import time
import asyncio

class Server:
    def __init__(self, host, port, durata_licitatie):
        self.host = host
        self.port = port
        self.durata_licitatie = durata_licitatie
        self.server_socket = None
        self.client_sockets = []
        self.client_names = []
        self.produse = {}
        self.produse_licitatie = []

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Serverul rulează pe {self.host}:{self.port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Nouă conexiune de la {client_address[0]}:{client_address[1]}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        client_name = self.receive_message(client_socket)
        if client_name in self.client_names:
            print(f"Conectare refuzată. Există deja un client cu numele {client_name}.")
            client_socket.close()
            return
        self.client_sockets.append(client_socket)
        self.client_names.append(client_name)
        # self.send_message(client_socket, "Conectare reușită.")
        if self.produse_licitatie:
            self.send_message(client_socket, f"Produse disponibile la licitatie:\n")
            for produs in self.produse_licitatie:
                self.send_message(client_socket,
                       f"Nume produs: {produs['nume_produs']}\n"
                       f"Vânzător: {produs['vanzator']}\n"
                       f"Pret minim: {produs['pret_minim']}\n"
                       f"Pret maxim: {produs['pret_maxim']}\n\n")
        else:
            self.send_message(client_socket, '\nInca nu sunt produse puse spre licitatie')

        while True:
            message = self.receive_message(client_socket)
            if message:
                self.process_message(client_name, message)
            else:
                break

        client_socket.close()
        self.client_sockets.remove(client_socket)
        self.client_names.remove(client_name)
        self.broadcast(f"{client_name} s-a deconectat.")

    def process_message(self, client_name, message):
        command_parts = message.strip().lower().split()
        # command = command_parts[0].lower()

        if command_parts[0] == "adauga" and command_parts[1] =='produs':
            if len(command_parts) == 4:
                nume_produs = command_parts[2]
                pret_minim = float(command_parts[3])
                self.adauga_produs(client_name, nume_produs, pret_minim)
            else:
                self.send_message_to_client(client_name, "Comandă incorectă. Utilizare: Adauga produs <nume_produs> <pret_minim>")
        elif command_parts[0] == "ofera":
            if len(command_parts) == 4:
                nume_produs = command_parts[1]
                oferta = float(command_parts[2])
                vanzator = command_parts[3]
                self.ofera(client_name, nume_produs, oferta, vanzator)
            else:
                self.send_message_to_client(client_name, "Comandă incorectă. Utilizare: Ofera <nume_produs> <oferta>")
        elif command_parts[0] == "incepe" and command_parts[1] == 'licitatia':
            if len(command_parts) == 3:
                nume_produs = command_parts[2]
                self.start_licitatie(client_name, nume_produs)
            else:
                self.send_message_to_client(client_name, "Comandă incorectă. Utilizare: Incepe licitatia <nume_produs>")
        else:
            self.send_message_to_client(client_name, "Comandă necunoscută.")

    def adauga_produs(self, nume_vanzator, nume_produs, pret_minim):
        if nume_vanzator not in self.produse:
            self.produse[nume_vanzator] = []
        
        x = 0
        for p in self.produse[nume_vanzator]:
            if p["nume_produs"] == nume_produs:
                x = 1

        if x==0:
            produs = {
                "nume_produs": nume_produs,
                "vanzator": nume_vanzator,
                "pret_minim": pret_minim,
                "pret_maxim": pret_minim,
                "valabil":True,
                "oferte": [],
                "oferta_maxima":{"cumparator":"", "oferta":0}
            }
            # self.produse_licitatie.append(produs)
            self.produse[nume_vanzator].append(produs)
            self.broadcast(f"Produs nou disponibil pentru licitație:\n"
                       f"Nume produs: {nume_produs}\n"
                       f"Vânzător: {nume_vanzator}\n"
                       f"Pret minim: {pret_minim}\n")
        else:
            self.send_message_to_client(nume_vanzator, 'Produsul deja exista')
        
    
    def ofera(self, nume_cumparator, nume_produs, oferta, nume_vanzator):
        produs = self.cauta_produs(nume_produs, nume_vanzator, nume_cumparator)
        if produs:
            # if produs["nume_produs"] not in produs["oferte"]:
            #     produs["oferte"][produs["nume_produs"]] = {"ofertator": nume_cumparator, "oferta": oferta}
            #     self.broadcast(f"{nume_cumparator} a făcut o ofertă pentru produsul {nume_produs}.")
                # if oferta > produs["pret_maxim"]:
                #     produs["pret_maxim"] = oferta
                #     produs["oferta_maxima"] = {"cumparator":nume_cumparator, "oferta": oferta}
                #     self.broadcast(f"Pretul maxim este acum de {oferta} u.m.")
            # else:
            #     self.send_message_to_client(nume_cumparator, f"Ați făcut deja o ofertă pentru produsul {nume_produs}.")
            if nume_cumparator != produs["vanzator"]:
                if nume_cumparator != produs["oferta_maxima"]["cumparator"]:
                    if oferta > produs["pret_maxim"]:
                        produs["pret_maxim"] = oferta
                        produs["oferta_maxima"] = {"cumparator":nume_cumparator, "oferta": oferta}
                        if nume_cumparator not in produs["oferte"]:
                            produs["oferte"].append(nume_cumparator)
                        for cumparator in produs["oferte"]:
                            self.send_message_to_client(cumparator, f"Pretul maxim pentru produsul {nume_produs} este acum de {oferta} u.m.") 
                    else:
                        self.send_message_to_client(nume_cumparator, "Nu puteti face o oferta mai mica decat pretul actual")
                else:
                    self.send_message_to_client(nume_cumparator, "Ati licitat deja pentru acest produs!")
            else:
                self.send_message_to_client(nume_cumparator, "Nu puteti licita pentru propriul produs!")
        else:
            self.send_message_to_client(nume_cumparator, f"Produsul {nume_produs} nu există în licitație.")

    def start_licitatie(self, clientName, denumire_produs):
        #TODO creeaza thread de timer care schimba booleanu in spate

        # for p in self.produse_licitatie:
        x = 0
        for p in self.produse[clientName]:
            if p["nume_produs"] == denumire_produs:
                x = 1
                if clientName == p["vanzator"]:
                    self.broadcast(f"Licitația a început pentru produsul {denumire_produs}.")
                    self.produse_licitatie.append(p)
                    p['oferte'].append(clientName)
                    self.broadcast(f"\nProdus: {p['nume_produs']}\n"
                                   f"Vânzător: {p['vanzator']}\n"
                                   f"Pret minim: {p['pret_minim']}\n"
                                   f"Pret maxim: {p['pret_maxim']}")
                    # timp = threading.Timer(self.durata_licitatie, self.process_message, args=(denumire_produs, ))
                    # timp.start()
                    # timp.join()
                    # self.broadcast("\nLicitația a expirat.")
                    # oferta_max = p["oferta_maxima"]["oferta"]
                    # cumparator = p["oferta_maxima"]["cumparator"]
                    # self.broadcast(f"\nPodusul {denumire_produs} nu mai este valabil!\nOferta maxima a fost de {oferta_max}, felicitari {cumparator}!")
                    task = threading.Thread(target=self.runInBackGround, args=(p, ))
                    task.start()
                else:
                    self.send_message_to_client(clientName, "Nu sunteti vanzatorul acestui obiect")
        if x == 0:
            self.send_message_to_client(clientName, 'Produsul nu exista')

        # time.sleep(self.durata_licitatie)


        self.marcaj_produse_indisponibile()

    async def licitatie_incheiata(self, produs):
        await asyncio.sleep(self.durata_licitatie)
        self.broadcast(f"\nLicitația a expirat pentru produsul {produs['nume_produs']}.")
        oferta_max = produs["oferta_maxima"]["oferta"]
        cumparator = produs["oferta_maxima"]["cumparator"]
        denumire_produs = produs["nume_produs"]
        self.broadcast(f"\nPodusul {denumire_produs} nu mai este valabil!\nOferta maxima a fost de {oferta_max}, felicitari {cumparator}!")
        #TODO scoate produsul din lista de produse
        self.produse_licitatie.remove(produs)
        vanzator = produs["vanzator"]
        self.produse[vanzator].remove(produs)


    def runInBackGround(self, produs):
        asyncio.run(self.licitatie_incheiata(produs))

    def marcaj_produse_indisponibile(self):
        for produs in self.produse_licitatie:
            produs["disponibil"] = False

    def cauta_produs(self, nume_produs, nume_vanzator, nume_cumparator):
        for produs in self.produse_licitatie:
            if produs["nume_produs"] == nume_produs and produs['vanzator'] == nume_vanzator:
                return produs
        return None

    def broadcast(self, message):
        for client_socket in self.client_sockets:
            self.send_message(client_socket, message)

    def send_message_to_client(self, client_name, message):
        client_index = self.client_names.index(client_name)
        client_socket = self.client_sockets[client_index]
        self.send_message(client_socket, message)

    def receive_message(self, client_socket):
        try:
            message = client_socket.recv(1024).decode()
            return message.strip()
        except:
            return ""

    def send_message(self, client_socket, message):
        try:
            client_socket.send(message.encode())
        except:
            pass


# Exemplu de utilizare
host = "localhost"
port = 12345
durata_licitatie = 180  # Durata licitației în secunde

server = Server(host, port, durata_licitatie)
server.start()


