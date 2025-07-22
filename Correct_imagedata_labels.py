import os
import json

def remove_image_data_from_all_json(target_dir, recursive=True):
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.json'):
                json_path = os.path.join(root, file)
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)

                    if 'imageData' in data:
                        data['imageData'] = None  # Or use: del data['imageData']
                        with open(json_path, 'w') as f:
                            json.dump(data, f, indent=4)
                        print(f"Cleaned: {json_path}")
                    else:
                        print(f"No imageData field: {json_path}")

                except Exception as e:
                    print(f"Failed to process {json_path}: {e}")
        if not recursive:
            break

# Replace with the path to your labelme annotation directory
if __name__ == "__main__":
    #target_directory = "G:/Gedeelde drives/Team_BioDiv/5_Projecten/2024_Biodiversa_habitatpilot/WP2_3/Inundation/Segmentation_orthos/Cropped_orthos_tiles/Kloosterbeemden/2020"
    #target_directory = "G:/Gedeelde drives/Team_BioDiv/5_Projecten/2024_Biodiversa_habitatpilot/WP2_3/Inundation/Segmentation_orthos/Cropped_orthos_tiles/Kloosterbeemden/2021"
    #target_directory = "G:/Gedeelde drives/Team_BioDiv/5_Projecten/2024_Biodiversa_habitatpilot/WP2_3/Inundation/Segmentation_orthos/Cropped_orthos_tiles/Kloosterbeemden/2023"
    #target_directory = "G:/Gedeelde drives/Team_BioDiv/5_Projecten/2024_Biodiversa_habitatpilot/WP2_3/Inundation/Segmentation_orthos/Cropped_orthos_tiles/Kloosterbeemden/2024"

    #target_directory = "G:/Gedeelde drives/Team_BioDiv/5_Projecten/2024_Biodiversa_habitatpilot/WP2_3/Inundation/Segmentation_orthos/Cropped_orthos_tiles/Schulensmeer/2020"
    #target_directory = "G:/Gedeelde drives/Team_BioDiv/5_Projecten/2024_Biodiversa_habitatpilot/WP2_3/Inundation/Segmentation_orthos/Cropped_orthos_tiles/Schulensmeer/2021"
    #target_directory = "G:/Gedeelde drives/Team_BioDiv/5_Projecten/2024_Biodiversa_habitatpilot/WP2_3/Inundation/Segmentation_orthos/Cropped_orthos_tiles/Schulensmeer/2023"
    target_directory = "G:/Gedeelde drives/Team_BioDiv/5_Projecten/2024_Biodiversa_habitatpilot/WP2_3/Inundation/Segmentation_orthos/Cropped_orthos_tiles/Schulensmeer/2024"



    remove_image_data_from_all_json(target_directory)