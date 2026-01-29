package main

import (
    "io"
    "net"
    "os"
    "time"
)

func main() {
    ln, err := net.Listen("tcp", "127.0.0.1:0")
    if err != nil {
        return
    }
    addr := ln.Addr().String()

    go func() {
        conn, err := ln.Accept()
        if err == nil {
            _, _ = conn.Write([]byte("hi"))
            _ = conn.Close()
        }
        _ = ln.Close()
    }()

    conn, err := net.Dial("tcp", addr)
    if err == nil {
        _, _ = io.ReadAll(conn)
        _ = conn.Close()
    }

    _ = os.WriteFile("demo_output.txt", []byte("hello"), 0644)
    time.Sleep(500 * time.Millisecond)
}
