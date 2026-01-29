import java.io.FileOutputStream;
import java.net.ServerSocket;
import java.net.Socket;

public class Main {
    public static void main(String[] args) throws Exception {
        ServerSocket server = new ServerSocket(0);
        int port = server.getLocalPort();

        Thread t = new Thread(() -> {
            try {
                Socket conn = server.accept();
                conn.getOutputStream().write("hi".getBytes());
                Thread.sleep(3000);
                conn.close();
                server.close();
            } catch (Exception e) {
                // ignore
            }
        });
        t.setDaemon(true);
        t.start();

        Socket client = new Socket("127.0.0.1", port);
        client.getInputStream().read();

        FileOutputStream out = new FileOutputStream("demo_output.txt");
        out.write("hello".getBytes());
        out.flush();

        try {
            new ProcessBuilder("cmd", "/c", "echo", "dynamic-java").start().waitFor();
        } catch (Exception e) {
            // ignore
        }

        Thread.sleep(3000);
        out.close();
        client.close();
    }
}
