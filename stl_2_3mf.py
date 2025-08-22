import numpy as np
from stl import mesh
import lib3mf
from lib3mf import get_wrapper

# Get version
def get_version(wrapper):
    major, minor, micro = wrapper.GetLibraryVersion()
    print("Lib3MF version: {:d}.{:d}.{:d}".format(major, minor, micro), end="")
    hasInfo, prereleaseinfo = wrapper.GetPrereleaseInformation()
    if hasInfo:
        print("-" + prereleaseinfo, end="")
    hasInfo, buildinfo = wrapper.GetBuildInformation()
    if hasInfo:
        print("+" + buildinfo, end="")
    print("")


# Create vertex in a mesh
def create_vertex(_mesh, x, y, z):
    position = lib3mf.Position()
    position.Coordinates[0] = float(x)
    position.Coordinates[1] = float(y)
    position.Coordinates[2] = float(z)
    _mesh.AddVertex(position)
    return position


# Add triangle in a mesh
def add_triangle(_mesh, p1, p2, p3):
    triangle = lib3mf.Triangle()
    triangle.Indices[0] = p1
    triangle.Indices[1] = p2
    triangle.Indices[2] = p3
    _mesh.AddTriangle(triangle)
    return triangle

if __name__ == "__main__":
    # Load in stl
    stl_mesh = mesh.Mesh.from_file('subsurface.stl')

    # Get a wrapper object
    wrapper = get_wrapper()

    # Check version always
    get_version(wrapper)

    # Create a model
    model = wrapper.CreateModel()
    model.SetUnit(lib3mf.ModelUnit.MilliMeter)
    mesh_object = model.AddMeshObject()

    # Extract all vertices from the mesh
    all_vertices = stl_mesh.points.reshape(-1, 3)

    # Find unique vertices and their inverse indices
    unique_vertices, inverse_indices = np.unique(all_vertices, axis=0, return_inverse=True)

    # Reshape inverse_indices to represent the faces (triangles)
    # Each row in faces will contain the indices of the three vertices forming a triangle
    faces = inverse_indices.reshape(-1, 3)

    vertices = []
    for v in unique_vertices:
        vertices.append(create_vertex(mesh_object, v[0], v[1], v[2]))

    triangles = []
    for t in faces:
        triangles.append(add_triangle(mesh_object, t[0], t[1], t[2]))

    # Set geometry to the mesh object after creating vertices and triangles
    mesh_object.SetGeometry(vertices, triangles)

    # Add build item with an identity transform
    model.AddBuildItem(mesh_object, wrapper.GetIdentityTransform())

    # Save the model to a 3MF file
    writer = model.QueryWriter("3mf")
    writer.WriteToFile("subsurface.3mf")