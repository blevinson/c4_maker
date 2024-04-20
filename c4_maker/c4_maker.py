import argparse
import importlib.util
import os
import inspect
from openai import OpenAI
from dotenv import load_dotenv
import re
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory where the script is located
sys.path.append(script_dir)  # Add the script's directory to the Python path

def load_module_from_file(filepath):
    # Convert relative path to absolute path
    filepath = os.path.abspath(filepath)
    directory, filename = os.path.split(filepath)
    module_name = os.path.splitext(filename)[0]

    # Add the directory to sys.path
    sys.path.insert(0, directory)

    try:
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module  # Add to sys.modules
        spec.loader.exec_module(module)
    finally:
        # Remove the directory from sys.path to avoid potential conflicts
        try:
            sys.path.remove(directory)
        except ValueError:
            pass

    return module


# Load environment variables and initialize the OpenAI client
load_dotenv("./env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

shot_1 = """
workspace {
  model {
    properties {
      "structurizr.groupSeparator" "/"
    }
    main_system = SoftwareSystem "Main System" "Main system handling all operations" {
      main_container = Container "Main Container" "Primary container for all components" {
        calculate_checksum = Component "calculate_checksum" "Calculate checksum of downloaded file" {
          technology "python"
        }
        download_file = Component "download_file" "Download the file from URL" {
          technology "python"
        }
        get_checksum_from_s3 = Component "get_checksum_from_s3" "Get the checksum from S3" {
          technology "python"
        }
        main = Component "main" "Main Application" {
          technology "python"
        }
        match_file_to_s3_folder = Component "match_file_to_s3_folder" "Match the filename with the S3 folder" {
          technology "python"
        }
        process_files_if_checksum_differs = Component "process_files_if_checksum_differs" "Process files if their checksum is different" {
          technology "python"
        }
        unzip_file = Component "unzip_file" "Unzip the download file" {
          technology "python"
        }
        upload_checksum_to_s3 = Component "upload_checksum_to_s3" "Upload the checksum to S3" {
          technology "python"
        }
        upload_file_to_s3 = Component "upload_file_to_s3" "Upload the file to S3" {
          technology "python"
        }
      }
    }
    download_file -> main "Downloading Files" "Component"
    main -> download_file "Uses" "Component"
    main -> calculate_checksum "Uses" "Component"
    main -> get_checksum_from_s3 "Uses" "Component"
    main -> process_files_if_checksum_differs "Uses" "Component"
    match_file_to_s3_folder -> main "Matching Files" "Component"
    process_files_if_checksum_differs -> unzip_file "Uses" "Component"
    process_files_if_checksum_differs -> upload_file_to_s3 "Uses" "Component"
    upload_checksum_to_s3 -> main "Uploading Check Sum" "Component"
    upload_file_to_s3 -> main "Uploading Files" "Component"
  }
  views {
    styles {
      element "Element" {
        shape "RoundedBox"
      }
      element "Software System" {
        background "#1168bd"
        color "#ffffff"
      }
      element "Container" {
        background "#438dd5"
        color "#ffffff"
      }
      element "Component" {
        background "#85bbf0"
        color "#000000"
      }
      element "Person" {
        background "#08427b"
        color "#ffffff"
        shape "Person"
      }
      element "Infrastructure Node" {
        background "#ffffff"
      }
      element "database" {
        shape "Cylinder"
      }
    }
  }
}

    """
shot_2 = """
    @c4_element('Component', label="Data Retrieval", technology="Python", description="Responsible for fetching data from external APIs and processes")
    def data_retrieval_component():
        pass
    
    @c4_element('Component', label="S3 Actions", technology="Python", description="Handles S3 bucket interactions such as creating, deleting, and uploading objects")
    def s3_actions_component():
        pass
    
    @c4_element('Component', label="Zip File Actions", technology="Python", description="Handles actions on zip file such as downloading and unzipping")
    def zip_file_actions_component():
        pass
    
    @c4_element('Component', label="Checksum Actions", technology="Python", description="Handles checksum comparisons and uploads checksums")
    def checksum_actions_component():
        pass
    
    @c4_element('Component', label="Main", technology="Python", description="Runs the main execution of the script")
    def main_component():
        pass
    
    @c4_relationship('main_component', 'data_retrieval_component', "Uses", "Component")
    def uses_relationship1():
        pass
    
    @c4_relationship('data_retrieval_component', 's3_actions_component', "Uses", "Component")
    def uses_relationship2():
        pass
    
    @c4_relationship('s3_actions_component', 'zip_file_actions_component', "Uses", "Component")
    def uses_relationship3():
        pass
    
    @c4_relationship('zip_file_actions_component', 'checksum_actions_component', "Uses", "Component")
    def uses_relationship4():
        pass
    
    @c4_relationship('checksum_actions_component', 'main_component', "Updates", "Component")
    def uses_relationship5():
        pass
    """


def estimate_tokens(text):
    """ Roughly estimate the number of tokens in the text based on whitespace. """
    return len(text.split())


def split_text_into_chunks(text, max_chunk_size=3000):
    """ Splits the text into manageable chunks according to the token limit. """
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        if estimate_tokens(' '.join(current_chunk + [word])) > max_chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk.append(word)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def generate_annotations(source_code):
    """Generates annotation for a given source code using OpenAI's API, handling large inputs by splitting them into chunks."""
    responses = []
    prompt = (
        f"YOU ARE NOT A HELPFUL ASSISTANT. JUST RESPOND IN CODE. DO NOT ADD EXPLANATIONS OR COMMENTS. Examine code and figure out Components and the relationships between them and how they should be organized"
        f"in containers. Look at this code on how to add decorators: {shot_2}. "
        f"Extract meaning from method name to create title. For example, if method name is 'download_file' name should be 'Downloads File'."
        f"Extract meaning from method description to create description. For example, if method name is 'download_file' description should be 'Downloads file from external source'."
        f"match_file_to_s3_folder should be 'Match File to S3 Folder'. "
        f"Use that and related elements to create description. "
        f"Here is a working example dsl code that is being created: {shot_1}"
        f"BE VERY CONSISTENT AND FORMAL WITH YOUR DECISIONS."
        f" DO NOT MAKE UP DIFFERENT FORMATING OF DECORATORS,"
        f"JUST CHANGE VALUES. Use @c4_relationship for relationships and @c4_element for components. DO NOT INCLUDE COMPONENTS AND RELATIONSHIPS WHICH ARE NOT "
        f" DO A STEP BY STEP ANALYSIS AND FIGURE OUT RELATIONSHIPS BETWEEN COMPONENTS AND THE DATA FLOW. ADD THE DECORATORS TO THIS CODE {source_code}. "
        f"DO NOT CHANGE ANYTHING OTHER THEN ADDING DOCORATORS."
    )
    chunks = split_text_into_chunks(prompt)

    for chunk in chunks:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "YOU ONLY RESPOND IN CODE WITH NO OTHER EXPLANATIONS OR COMMENTS. FIGURE OUT THE "
                                              "RELATIONSHIPS BETWEEN COMPONENTS. Add 'pass' after each method so it "
                                              "doesn't cause errors."},
                {"role": "user", "content": chunk}
            ]
        )
        responses.append(response.choices[0].message.content.strip())

    return " ".join(responses)


def check_missing_relationships(elements, relationships):
    defined_components = set(elements.keys())
    referenced_components = set()

    for rel in relationships:
        referenced_components.add(rel['source'])
        referenced_components.add(rel['target'])

    missing_components = referenced_components - defined_components
    if missing_components:
        print("Missing component definitions for:")
        for component in missing_components:
            print(component)
    else:
        print("No missing components.")


def c4_element(type_, **kwargs):
    def decorator(func):
        if not hasattr(func, 'c4_details'):
            func.c4_details = {}
        func.c4_details['type'] = type_
        func.c4_details.update(kwargs)
        return func

    return decorator


def c4_relationship(source, target, description, technology=""):
    def decorator(func):
        if not hasattr(func, 'c4_relationships'):
            func.c4_relationships = []
        func.c4_relationships.append(
            {'source': source, 'target': target, 'description': description, 'technology': technology})
        return func

    return decorator


def generate_plantuml(elements, relationships):
    lines = [
        '@startuml',
        '!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml',
        'title Component diagram for application'
    ]
    check_missing_relationships(elements, relationships)
    for el in elements.values():
        lines.append(
            f'Component("{el.__name__}", "{el.c4_details["label"]}", "{el.c4_details["technology"]}", "{el.c4_details["description"]}")')
    for rel in relationships:
        lines.append(f'Rel("{rel["source"]}", "{rel["target"]}", "{rel["description"]}", "{rel["technology"]}")')
    lines.append('@enduml')
    return '\n'.join(lines)


def workspace_to_dsl(workspace):
    dsl_output = ""

    # Retrieve the first model from the workspace if 'models' is a list or similar collection.
    # This is just an example; you'll need to adjust this based on how the 'models' are actually stored or accessed.
    model = workspace.models[0]

    # Convert model.elements dictionary to a list of tuples (name, element)
    elements_data = [(name, element) for name, element in model.elements.items()]

    # Iterate through the elements data list
    for name, element in elements_data:
        dsl_output += f"element {name} {{\n"
        dsl_output += f"  description {element.description}\n"
        # Add other properties and relationships as needed
        dsl_output += "}\n"

    # Return the DSL representation as a string
    return dsl_output


from pystructurizr.dsl import Workspace, Model, Component, Container, Person, SoftwareSystem

def generate_structurizr_dsl(elements, relationships):
    workspace = Workspace()
    model = Model(name='Application')
    workspace.models.append(model)

    main_system = SoftwareSystem(name="Main System", description="Main system handling all operations")
    model.elements.append(main_system)

    # Extract container name from module name
    container_name = __name__.split('.')[-1] + " Container"  # Assuming the module name gives a meaningful container name

    main_container = Container(name=container_name, description="Primary container for all components")
    main_system.elements.append(main_container)

    # Create a mapping from function names to labels for easier access
    name_to_label = {el_name: el_func.c4_details.get('label', el_name) for el_name, el_func in elements.items()}

    # Create components and add to the main container using the 'label' for the component name
    for el_name, el_func in elements.items():
        el_details = el_func.c4_details
        component_label = name_to_label[el_name]  # Get label from mapping
        component = Component(name=component_label, description=el_details['description'], technology=el_details.get('technology', 'Python'))
        main_container.elements.append(component)

    # Adjust relationships to use labels
    for rel in relationships:
        source_label = name_to_label.get(rel['source'], rel['source'])  # Get source label from mapping, fallback to source name
        target_label = name_to_label.get(rel['target'], rel['target'])  # Get target label from mapping, fallback to target name
        source_component = next((comp for comp in main_container.elements if comp.name == source_label), None)
        target_component = next((comp for comp in main_container.elements if comp.name == target_label), None)
        if source_component and target_component:
            source_component.uses(target_component, description=rel.get('description', ''), technology=rel.get('technology', ''))

    return workspace


def sanitize_identifier(name):
    # Replace spaces with underscores and remove disallowed characters
    sanitized = re.sub('[^a-zA-Z0-9_-]', '', name.replace(' ', '_'))
    return sanitized


def setup_workspace():
    workspace = Workspace()

    # Create elements
    user = Person("User", "A user of my software system.")
    software_system = SoftwareSystem("Main Software System", "My software system.")

    # Create a model and add elements to it
    model = workspace.Model(name="My Model")
    model.Person(user)
    model.SoftwareSystem(software_system)

    return workspace.dump()


def main():

    parser = argparse.ArgumentParser(description="Generate architecture diagrams from Python code.")
    parser.add_argument('filepath', type=str, help='Path to the Python file to analyze.')
    parser.add_argument('--annotate', action='store_true', help='Generate annotation for the code.')
    parser.add_argument('--plantuml', action='store_true', help='Generate a PlantUML diagram.')
    parser.add_argument('--dsl', action='store_true', help='Generate a Structurizr DSL diagram.')
    args = parser.parse_args()

    full_path = os.path.abspath(args.filepath)

    # Check if the file exists at the specified path
    if not os.path.isfile(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return

    if not args.filepath.endswith('.py'):
        print("Error: The file must be a Python '.py' file.")
        return
    module = None
    module_name = args.filepath.rstrip('.py')

    try:
        module = load_module_from_file(args.filepath)
        # Use the module for further processing
        if module is not None:
            # ... continue with processing ...
            try:
                source_code = inspect.getsource(module)
            except TypeError as e:
                print(f"Error processing the module: {e}")
                return
        else:
            print("Failed to load and process the module.")
            return
        source_code = inspect.getsource(module)
        # Proceed with your code logic using `source_code`
    except FileNotFoundError:
        print(f"Error: The file {args.filepath} does not exist.")
    except ModuleNotFoundError as e:
        print(f"Error loading module: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    elements, relationships = None, None  # Initialize these to None to handle possible checks later

    if args.annotate:
        imports = 'from c4_maker import c4_element, c4_relationship \n'
        source_code = inspect.getsource(module)
        annotation_code = generate_annotations(source_code)
        output_filename = f'{module_name}_annotated.py'
        with open(output_filename, 'w') as file:
            file.write(imports + annotation_code)
        print(f"Annotated code written to {output_filename}")

    # Check if any diagram generation is requested
    if args.plantuml or args.dsl:
        # Prepare elements and relationships for diagram generation
        elements = {name: obj for name, obj in inspect.getmembers(module) if hasattr(obj, 'c4_details')}
        relationships = [rel for _, obj in inspect.getmembers(module) for rel in getattr(obj, 'c4_relationships', [])]

    if args.plantuml:
        print("Generating PlantUML diagram...")
        plantuml_code = generate_plantuml(elements, relationships)
        output_filename = f'{module_name}.puml'
        with open(output_filename, 'w') as file:
            file.write(plantuml_code)
        print(f"PlantUML diagram written to {output_filename}")

    if args.dsl:
        print("Generating Structurizr DSL diagram...")
        structurizr_dsl = generate_structurizr_dsl(elements, relationships)
        dsl_filename = f'{module_name}.dsl'
        # dsl_filename = '/Users/brant/structurizr/workspace.dsl'
        with open(dsl_filename, 'w') as file:
            file.write(str(structurizr_dsl.dump()))
        print(f"Structurizr DSL diagram written to {dsl_filename}")

    if not (args.plantuml or args.dsl or args.annotate):
        print("No output format specified. Use --plantuml or --dsl to generate diagrams.")
        return


if __name__ == "__main__":
    main()
