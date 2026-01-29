import java.io.FileWriter;
import java.io.IOException;
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
                conn.close();
                server.close();
            } catch (IOException e) {
                // ignore
            }
        });
        t.setDaemon(true);
        t.start();

        Socket client = new Socket("127.0.0.1", port);
        client.getInputStream().read();
        client.close();

        try (FileWriter writer = new FileWriter("demo_output.txt")) {
            writer.write("hello");
        }
        Thread.sleep(500);
    }
}
