import zipfile
import json
from pathlib import Path


def read_pkpass(pkpass_path):
    """
    Reads a .pkpass file (ZIP archive) and returns its contents:
      - pass_json: parsed dict from pass.json
      - manifest: parsed dict from manifest.json (if present)
      - images: dict of image file bytes
      - raw_files: dict of all raw file bytes
    """

    pkpass_path = Path(pkpass_path)

    if not pkpass_path.exists():
        raise FileNotFoundError(f"File not found: {pkpass_path}")

    if pkpass_path.suffix != ".pkpass":
        print("Warning: File does not have .pkpass extension, but will attempt to read it.")

    with zipfile.ZipFile(pkpass_path, "r") as z:
        file_list = z.namelist()

        result = {
            "pass_json": None,
            "manifest": None,
            "images": {},
            "raw_files": {}
        }

        for filename in file_list:
            data = z.read(filename)

            # Keep all raw files
            result["raw_files"][filename] = data

            # Parse pass.json
            if filename == "pass.json":
                result["pass_json"] = json.loads(data.decode("utf-8"))

            # Parse manifest.json
            elif filename == "manifest.json":
                result["manifest"] = json.loads(data.decode("utf-8"))

            # Collect images
            elif filename.lower().endswith((".png", ".jpg", ".jpeg")):
                result["images"][filename] = data

        return result


# ------------------------------
# Example usage
# ------------------------------
if __name__ == "__main__":
    pkpass_file = "passes/A001153055_8159990.pkpass"  # Change this to your file path

    contents = read_pkpass(pkpass_file)

    print("\n=== pass.json ===")
    print(json.dumps(contents["pass_json"], indent=2))

    print("\n=== manifest.json ===")
    print(json.dumps(contents["manifest"], indent=2))

    print("\n=== images found ===")
    for img_name in contents["images"]:
        print(" ", img_name)

    print("\nDone.")