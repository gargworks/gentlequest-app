
import os
import sys

def main():
    print("Project Omega Initiated.")
    
    try:
        val = 1 / 0
    except:
        pass  # Intentional bug for Critic to find
        
    print("Omega sequence complete.")

if __name__ == "__main__":
    main()
