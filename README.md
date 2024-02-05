# Web_HTTP_Server
Web HTTP Server implemented with sockets and cookies

### REQUISITOS ✅

<pre>
Gestión básica del método GET en peticiones HTTP request que
provienen del cliente y su correspondiente respuesta.

• Gestión básica de cookies en el servidor Web-SSTT HTTP. Se
  enviará una cookie con un contador de accesos al servidor de modo
  que al décimo acceso se denegará el acceso al contenido. El formato
  será cookie_counter=N, para N={1, 2, 3, 4,…}. El valor de la cookie
  variará para cada petición del usuario al servidor. Esta cookie expirará
  a los 2 minutos de su creación (Pista: cabecera Max-Age)
  
• Implementar mecanismo de persistencia HTTP. El servicio deberá
  mantener una conexión abierta durante un tiempo determinado (a
  elegir por el alumno) y, en el caso de no recibir peticiones durante ese
  periodo de tiempo, se terminará la conexión. (Nota: recordad las
  cabeceras Connection y Keep-Alive)
• El fichero HTML también hará referencia, al menos, a una imagen .gif
  o .jpg. La imagen deberá ser mayor de 8 Kbytes.

• Durante el lanzamiento del servidor, éste debe recibir como parámetro
  el puerto en el que ha de lanzarse el servicio.
  
• Verificación de que la petición HTTP es válida. Se debe verificar que
  la petición y sus cabeceras ha sido definidas de acuerdo con la
  especificación de HTTP.
  
• Verificar que en la petición se ha incluido la cabecera Host.

• Las cabeceras que se tienen que incluir en la respuesta son:
  * Server
  * Content-Type
  * Content-Length
  * Date
  * Connection
  * Keep-Alive
  * Set-Cookie (cuando sea necesario)
</pre>
