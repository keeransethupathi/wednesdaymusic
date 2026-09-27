import sys
import uvicorn

if __name__ == "__main__":
    print("==============================================")
    print("  Launching Wednesday Songs (Vercel Edition)  ")
    print("==============================================")
    print("Local URL: http://localhost:3000")
    print("Press Ctrl+C to stop.")
    print("==============================================")
    
    try:
        uvicorn.run("api.index:app", host="0.0.0.0", port=3000, reload=True)
    except KeyboardInterrupt:
        print("\n[System] Wednesday Songs server stopped.")
    except Exception as e:
        print(f"\n[System] Error launching server: {e}")
        sys.exit(1)
