# Correct Deterministic Builder Content

# This content represents the deterministic builder functionality

def build_pvc(deterministic=True):
    if deterministic:
        print("Building PVC using deterministic method...")
    else:
        print("Building PVC using non-deterministic method...")

# Example usage
if __name__ == '__main__':
    build_pvc()