# coding=utf-8
#!/usr/bin/env python3


import socket
import selectors    #https://docs.python.org/3/library/selectors.html
import select
import types        # Para definir el tipo de datos data
import argparse     # Leer parametros de ejecución
import os           # Obtener ruta y extension
from datetime import datetime, timedelta # Fechas de los mensajes HTTP
import time         # Timeout conexión
import sys          # sys.exit
import re           # Analizador sintáctico
import logging      # Para imprimir logs

RE_HTTP=re.compile(r"HTTP\/1\.1")
RE_GET=re.compile(r"^GET")
RE_POST=re.compile(r"^POST")
RE_POST_BODY=re.compile(r"\\r\\n\\r\\n.*")
RE_URL=re.compile(r"www.* ")
RE_URL_PARAMETERS=re.compile(r"\?.* ")
RE_RECURSO=re.compile(r"GET \/.* ")
RE_HEADERS=re.compile(r"\\r\\n.*\\r\\n\\r\\n")
RE_COOKIE=re.compile(r"Cookie: [A-Za-z_0-9]+=[0-9]+")
RE_COOKIE_COUNTER=re.compile(r"Cookie: cookie_counter_[0-9]+=[0-9]+",2)


CORRECT_EMAIL= "usuario1%40foropatinetes8656.org"

BUFSIZE = 8192 # Tamaño máximo del buffer que se puede utilizar
TIMEOUT_CONNECTION = 35 # Timout para la conexión persistente
MAX_ACCESOS = 10 
BACK_LOG = 64   
MAX_KEEP_ALIVE_COUNTER=5

# Extensiones admitidas (extension, name in HTTP)
filetypes = {"gif":"image/gif", "jpg":"image/jpg", "jpeg":"image/jpeg", "png":"image/png", "htm":"text/htm", 
             "html":"text/html", "css":"text/css", "js":"text/js"}

# Configuración de logging
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s.%(msecs)03d] [%(levelname)-7s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()

headers_map={}
actual_cookie=0


def enviar_mensaje(cs, data):
    """ Esta función envía datos (data) a través del socket cs
        Devuelve el número de bytes enviados.
    """
    
    return cs.send(data)



def recibir_mensaje(cs):
    """ Esta función recibe datos a través del socket cs
        Leemos la información que nos llega. recv() devuelve un string con los datos.
    """
    return cs.recv(BUFSIZE).decode()



def cerrar_conexion(cs):
    """ Esta función cierra una conexión activa.
    """
    cs.close()


def print_headers():

    logging.info("headers=\n")

    for header in headers_map:
        logging.info(header)
        logging.info(":"+headers_map[header])


def send_bytes(cs,file,size):


    file_open=open(file,"rb")

    data=file_open.read(BUFSIZE)

    sended=0
    
    while sended<size:

        sended+=cs.send(data)
        data=file_open.read(BUFSIZE)

    file_open.close()


def send_file(msg,cs):

    global headers_map
    global actual_cookie


    flag=0
    


    if msg=="403":

        resp="403 Forbidden\r\n"
        file="403.html"

    elif msg=="401":

        resp="401 Unauthorized\r\n"
        file="401.html"
    
    elif msg=="404":

        resp="404 Not Found\r\n"
        file="404.html"
    
    elif msg=="405":

        resp="405 Method Not Allowed\r\n"
        file="405.html"

    elif msg=="406":

        resp=" 406 Not Acceptable\r\n"
        file="406.html"

    elif msg=="400":

        resp=" 400 Bad Request\r\n"
        file="400.html"

    elif msg=="505":

        resp="505 HTTP Version Not Supported\r\n"
        file="505.html"

    elif msg=="200":
        resp="200 OK\r\n"
        file="200.html"


    else:

        flag=1
        resp="200 OK\r\n"
        file=str(msg)
        

    size=os.stat(file).st_size
    file_type=os.path.basename(file).split(".")[1]

    if flag==1:

        file_type = filetypes[msg[1:].split(".")[1]]
        logging.info(file_type)

        resp="HTTP/1.1 "+resp+"Content-Type:"+file_type+"\r\n"+"Content-Length: "+str(size)+"\r\n"+"Date:"+datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')+"\r\n"+"Server: foropatinetes_8656.org\r\n"+ "Connection: Keep-Alive\r\n"+"Keep-Alive: timeout="+str(TIMEOUT_CONNECTION)+ ", max=5\r\n"+"Set-cookie: cookie_counter_8656="+str(actual_cookie)+" ;Max-Age=25"+"\r\n"+"\r\n"
    
    else:

        resp="HTTP/1.1 "+resp+"Content-Type:"+" text/html"+"\r\n"+"Content-Length: "+str(size)+"\r\n"+"Date:"+datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')+"\r\n"+ "Connection: Keep-Alive\r\n"+"Keep-Alive: timeout="+str(TIMEOUT_CONNECTION)+ ", max=5\r\n"+"\r\n"

    # logging.warning("respuesta=\n"+repr(resp))

    enviar_mensaje(cs,resp.encode())

    send_bytes(cs,file,size)




    '''
    HTTP/1.1 200 OK\r\n
    Date: Sun, 26 Sep 2010 20:09:20 GMT\r\n
    Server: Apache/2.0.52 (CentOS)\r\n
    Last-Modified: Tue, 30 Oct 2007 17:00:02 GMT\r\n
    ETag: "17dc6-a5c-bf716880"\r\n
    Accept-Ranges: bytes\r\n
    Content-Length: 2652\r\n
    Keep-Alive: timeout=10, max=100\r\n
    Connection: Keep-Alive\r\n
    Content-Type: text/html; charset=ISO-8859-1\r\n
    \r\n
    data data data data data ... 
    '''

    '''Server
    o Content-Type
    o Content-Length
    o Date
    o Connection
    o Keep-Alive
    o Set-Cookie (cuando sea necesario)
    '''



def process_headers(headers,cs):

    #* splitear por \r\n
    #* para todos mostrar lo que haya dsp de :

    headers_map= {}

    headers=headers.split("\\r\\n")

    for header in headers:

        if(header!=""):
            
            header=header.split(":")
            
            index=header[0].replace(" ","")

            value=header[1].replace(" ","")

            headers_map[index]=value

    #logging.warning("headers =\n"+headers_map)
    return headers_map
    

def process_cookies(headers,  cs):

    cookie=re.findall(RE_COOKIE,repr(headers))

    if cookie:

        cookie=cookie[0]
        cookie_counter=re.findall(RE_COOKIE_COUNTER,repr(cookie))

        if cookie_counter:

            cookie_counter=cookie_counter[0]

            counter=cookie_counter.replace(" ","")
            counter=counter.split("=")
            counter=int(counter[1])

            if counter==MAX_ACCESOS:
                #send_file("403",cs)
                return MAX_ACCESOS

            elif counter<MAX_ACCESOS and counter>=1:
                #counter+=1SSS
                return counter
        
        else:
            return 1
    else:
        return 0#*NUEVOS , SI NO HAY COOKIES DEVOLVEMOS 0


    """ Esta función procesa la cookie cookie_counter
        1. Se analizan las cabeceras en headers para buscar la cabecera Cookie
        2. Una vez encontrada una cabecera Cookie se comprueba si el valor es cookie_counter
        3. Si no se encuentra cookie_counter , se devuelve 1
        4. Si se encuentra y tiene el valor MAX_ACCESSOS se devuelve MAX_ACCESOS
        5. Si se encuentra y tiene un valor 1 <= x < MAX_ACCESOS se incrementa en 1 y se devuelve el valor
    """

def process_post_request(cs,msg):

    # logging.info(repr(msg))

    # \\r\\n\\r\\nemail=usuario1%40mARTket.org'
    
    email=re.findall(RE_POST_BODY,repr(msg))


    if email:
        email=email[0].strip()
        email=email.replace("'","")
        email=email.replace("\\r\\n","")
        email=email.replace("email=","")
        logging.info(email)

        
        if email==CORRECT_EMAIL:

            send_file("200", cs)

        else:

            send_file("401", cs)
        

    else:

        send_file("401", cs)
        


        

def process_web_request(cs, webroot):  

    global headers_map
    global actual_cookie

    keep_alive_counter=0

    
    

    while True:

        
        rsublist, wsublist, xsublist=select.select([cs],[], [],TIMEOUT_CONNECTION)

        #if keep_alive_counter>=MAX_KEEP_ALIVE_COUNTER:

            # msg= "Error : Número máximo de peticiones alcanzado [KEEP-ALIVE]\n"

            # #enviar_mensaje(cs, msg.encode()) 
            # cerrar_conexion(cs)
            # logging.info("Error : Número máximo de peticiones alcanzado [KEEP-ALIVE]")
            
            # return

            #msg= "Error : Timeout alcanzado 2\n"

            #enviar_mensaje(cs, msg.encode()) 
            #cerrar_conexion(cs)
            #logging.info("Timeout alcanzado  2")
            
            #return
            
            

        if rsublist:

            keep_alive_counter+=1



            
            msg = recibir_mensaje(cs)


            if keep_alive_counter>=MAX_KEEP_ALIVE_COUNTER:

                    logging.info("keep alive denteo de todo")
                    return

            #logging.info(repr(msg))

            if re.match(RE_POST, msg):
                process_post_request(cs,msg)
                continue
            
            elif not re.findall(RE_HTTP,msg) :# si encontramos http correcto
                send_file("505", cs)
                continue

            elif not re.findall(RE_GET,msg) :# si encontramos get correcto
                send_file("405",cs)
                continue

            if re.findall(RE_URL_PARAMETERS,msg):
                msg=re.sub(RE_URL_PARAMETERS," ",msg)


            recurso=re.findall(RE_RECURSO,msg)

            if recurso:


                
                
                recurso=recurso[0].replace("GET","")
                recurso=recurso.replace(" ","")

                recurso=recurso.replace("HTTP","")
                # logging.warning(recurso)

                if recurso=="/":
                    recurso="index.html"
                    recurso=webroot+recurso

                else:
    
                    recurso=recurso.replace("/","")
                    recurso=recurso.replace(" ","")
                    recurso=webroot+recurso


                # logging.info("recurso= "+recurso)


                headers=re.findall(RE_HEADERS,repr(msg))



                if not os.path.isfile(recurso):
                    send_file("404",cs)
                    
                

                elif headers:

                    headers_map=process_headers(headers[0],cs)
                    #print_headers()

                    ret_cookies=process_cookies(headers[0],cs)



                        

                    if ret_cookies==MAX_ACCESOS: # desconectar del servidor + send error
                        

                        
                        send_file("403", cs)
                        logging.info("LImite de accesos")

                        
                        
                        return 

                    else:#TODO añadir set cookies del valor

                        actual_cookie=ret_cookies+1

                    # logging.info("actual_cookie "+str(actual_cookie))

                        size=os.stat(recurso).st_size
                        file_type=os.path.basename(recurso).split(".")[1]
                                        
                        send_file(recurso, cs)
                


            else:
                send_file("400",cs)
                

        else:

            msg= "Error : Timeout alcanzado\n"

            enviar_mensaje(cs, msg.encode()) 
            logging.info("Timeout alcanzado")
            cerrar_conexion(cs)
            
            return

            


        


    """ Procesamiento principal de los mensajes recibidos.
        Típicamente se seguirá un procedimiento similar al siguiente (aunque el alumno puede modificarlo si lo desea)

        * Bucle para esperar hasta que lleguen datos en la red a través del socket cs con select()

            *#? Se comprueba si hay que cerrar la conexión por exceder TIMEOUT_CONNECTION segundos
             #? sin recibir ningún mensaje o hay datos. Se utiliza select.select

            * Si no es por timeout y hay datos en el socket cs.
                *#? Leer los datos con recv.
                * Analizar que la línea de solicitud y comprobar está bien formateada según HTTP 1.1
                    *#? Devuelve una lista con los atributos de las cabeceras.
                    *#? Comprobar si la versión de HTTP es 1.1
                    *#? Comprobar si es un método GET. Si no devolver un error Error 405 "Method Not Allowed".
                    *#? Leer URL y eliminar parámetros si los hubiera
                    *#? Comprobar si el recurso solicitado es /, En ese caso el recurso es index.html
                    *#? Construir la ruta absoluta del recurso (webroot + recurso solicitado)
                    *#? Comprobar que el recurso (fichero) existe, si no devolver Error 404 "Not found"
                    *#? Analizar las cabeceras. Imprimir cada cabecera y su valor. Si la cabecera es Cookie comprobar
                      #?el valor de cookie_counter para ver si ha llegado a MAX_ACCESOS.
                      #?Si se ha llegado a MAX_ACCESOS devolver un Error "403 Forbidden"
                    *#? Obtener el tamaño del recurso en bytes.
                    *#? Extraer extensión para obtener el tipo de archivo. Necesario para la cabecera Content-Type
                    *#? Preparar respuesta con código 200. Construir una respuesta que incluya: la línea de respuesta y
                     #? las cabeceras Date, Server, Connection, Set-Cookie (para la cookie cookie_counter),
                      #?Content-Length y Content-Type.
                    *#? Leer y enviar el contenido del fichero a retornar en el cuerpo de la respuesta.
                    *#? Se abre el fichero en modo lectura y modo binario
                        *#? Se lee el fichero en bloques de BUFSIZE bytes (8KB)
                        *#? Cuando ya no hay más información para leer, se corta el bucle

            *#? Si es por timeout, se cierra el socket tras el período de persistencia.
                * NOTA: Si hay algún error, enviar una respuesta de error con una pequeña página HTML que informe del error.
    """


def main():
    """ Función principal del servidor
    """

    try:

        # Argument parser para obtener la ip y puerto de los parámetros de ejecución del programa. IP por defecto 0.0.0.0
        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--port", help="Puerto del servidor", type=int, required=True)
        parser.add_argument("-ip", "--host", help="Dirección IP del servidor o localhost", required=True)
        parser.add_argument("-wb", "--webroot", help="Directorio base desde donde se sirven los ficheros (p.ej. /home/user/mi_web)")
        parser.add_argument('--verbose', '-v', action='store_true', help='Incluir mensajes de depuración en la salida')
        args = parser.parse_args()


        if args.verbose:
            logger.setLevel(logging.DEBUG)

        logger.info('Enabling server in address {} and port {}.'.format(args.host, args.port))

        logger.info("Serving files from {}".format(args.webroot))


        
        first_socket=socket.socket(family=socket.AF_INET,type=socket.SOCK_STREAM, proto=0)

        first_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR ,1 ) 

        if first_socket.bind((args.host,args.port))==-1:

            sys.exit("Error : No se ha podido realizar el bind()")

        
        first_socket.listen(BACK_LOG)


        
        while True:

            child_socket,child_addr = first_socket.accept()



            pid=os.fork()

            if pid==0:#hijo

                first_socket.close()
                process_web_request(child_socket, args.webroot)
                sys.exit()

            else:#padre
                    
                child_socket.close()
                

        """ Funcionalidad a realizar
        * Crea un socket TCP (SOCK_STREAM)

        * Permite reusar la misma dirección previamente vinculada a otro proceso. Debe ir antes de sock.bind
        * Vinculamos el socket a una IP y puerto elegidos

        * Escucha conexiones entrantes

        * Bucle infinito para mantener el servidor activo indefinidamente
            - Aceptamos la conexión

            - Creamos un proceso hijo

            - Si es el proceso hijo se cierra el socket del padre y procesar la petición con process_web_request()

            - Si es el proceso padre cerrar el socket que gestiona el hijo.
        """
    except KeyboardInterrupt:
        True

if __name__== "__main__":
    main()
