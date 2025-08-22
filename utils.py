import cv2
import numpy as np
import matplotlib.pyplot as plt
import lib3mf
import struct
from stl import mesh

def write_binary_stl(filename, facets):
    
    problem_cnt = 0    
    # Open file and set to write in binary
    with open(filename, 'wb') as f:
        
        # ASCII header (can/will be empty)
        f.write(b'\x00' * 80)

        # Write number of facets
        f.write(struct.pack('<I', len(facets))) # <I for little-endian unsigned

        # Write each facet
        for i, tri in enumerate(facets):

            if tri.zero_area():
                continue

            if any([prop is None for prop in [tri.v1, tri.v2, tri.v3, tri.normal]]):
                problem_cnt += 1
                continue

            if tri.v1[2] < 0 or tri.v2[2] < 0 or tri.v3[2] < 0:                
                problem_cnt += 1
                continue

            # Pack normal vector (3x float)
            f.write(struct.pack('<fff', tri.normal[0], tri.normal[1], tri.normal[2]))

            # Pack verts (3x(3x floats))
            f.write(struct.pack('<fff', tri.v1[0], tri.v1[1], tri.v1[2]))
            f.write(struct.pack('<fff', tri.v2[0], tri.v2[1], tri.v2[2]))
            f.write(struct.pack('<fff', tri.v3[0], tri.v3[1], tri.v3[2]))

            # Pack attribute byte count (2-byte unsigned short, usually 0)
            f.write(struct.pack('<H', 0))

    print(f'Wrote binary STL file {filename} with {3*len(facets)} vertices')

    if problem_cnt > 0:
        raise Exception(f'{problem_cnt} facets had problems and were omitted from the model!')

# Get version
def get_lib3mf_version(wrapper):
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
def create_3mf_vertex(_mesh, x, y, z):
    position = lib3mf.Position()
    position.Coordinates[0] = float(x)
    position.Coordinates[1] = float(y)
    position.Coordinates[2] = float(z)
    _mesh.AddVertex(position)
    return position


# Add triangle in a mesh
def add_3mf_triangle(_mesh, p1, p2, p3):
    triangle = lib3mf.Triangle()
    triangle.Indices[0] = p1
    triangle.Indices[1] = p2
    triangle.Indices[2] = p3
    _mesh.AddTriangle(triangle)
    return triangle

def convert_stl_to_3mf(stl_path, units='mm'):
    # Load in stl
    stl_mesh = mesh.Mesh.from_file(stl_path)

    # Get a wrapper object
    wrapper = lib3mf.get_wrapper()

    # Check version always
    get_lib3mf_version(wrapper)

    # Create a model
    model = wrapper.CreateModel()
    mesh_object = model.AddMeshObject()

    # Set chosen units
    if units.lower() in ['mm','millimeter','millimeters']:
        unit_selection = lib3mf.ModelUnit.MilliMeter
    elif units.lower() in ['in', 'inch', 'inches']:
        unit_selection = lib3mf.ModelUnit.Inch
    else:
        raise Exception('Method does not support given units: {units}')

    model.SetUnit(unit_selection)    

    # Extract all vertices from the mesh
    all_vertices = stl_mesh.points.reshape(-1, 3)

    # Find unique vertices and their inverse indices
    unique_vertices, inverse_indices = np.unique(all_vertices, axis=0, return_inverse=True)

    # Reshape inverse_indices to represent the faces (triangles)
    # Each row in faces will contain the indices of the three vertices forming a triangle
    faces = inverse_indices.reshape(-1, 3)

    vertices = []
    for v in unique_vertices:
        vertices.append(create_3mf_vertex(mesh_object, v[0], v[1], v[2]))

    triangles = []
    for t in faces:
        triangles.append(add_3mf_triangle(mesh_object, t[0], t[1], t[2]))

    # Set geometry to the mesh object after creating vertices and triangles
    mesh_object.SetGeometry(vertices, triangles)

    # Add build item with an identity transform
    model.AddBuildItem(mesh_object, wrapper.GetIdentityTransform())

    # Save the model to a 3MF file
    save_filepath = stl_path.split('.')[0] + '.3mf'
    writer = model.QueryWriter("3mf")
    writer.WriteToFile(save_filepath)

    print(f'Wrote 3MF file {save_filepath} with {len(unique_vertices)} vertices')

FIGURES = []
def show_img(img, fig_name=None, cmap=None, bgr=False):
    FIGURES.append(plt.figure(fig_name))

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if bgr else img

    plt.axis('off')
    plt.imshow(img, cmap=cmap)
    plt.show()
    
def zero_area_tri(v1, v2, v3):
    return np.any(np.cross((v2 - v1), (v3 - v2)))

def compute_tri_normal(cls, v1, v2, v3):
    cp   = np.cross((v2 - v1), (v3 - v2))
    norm = np.linalg.norm(cp)
    return cp / norm

def crop_to_aspect_ratio(img, ar, centered=False, offset=None):
    # Crop image to match the provided aspect ratio,
    # which is given by width/height

    img_h, img_w = img.shape[:2]
    ar_curr = img_w / img_h

    # Check if it's already correctly-sized
    if ar_curr == ar:
        return img

    if ar_curr > ar:
        # image is wider than ar, and need to trim dim=1
        new_w, new_h = int(round(img_h * ar)), img_h
    else:
        # image is tallen than ar, and need to trim dim=0
        new_w, new_h = img_w, int(round(img_w / ar))

    start_x, start_y = 0, 0
    if centered:
        start_x = int((img_w - new_w) // 2)
        start_y = int((img_h - new_h) // 2)
    elif offset is not None:
        start_x, start_y = offset

    return img[start_y:(start_y + new_h), start_x:(start_x + new_w),:]

# Phasing out this class >
class STL_Tri:
    def __init__(self, v1=None, v2=None, v3=None, normal=None):
        # v1 -> v2 -> v3 must be defined in a counter-clockwise manner,
        # such that the right-handed normal vector points outward from object interior
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

        # If normal is set at instantiation, then we won't implicitly compute it from vertices
        self.normal = normal
        self.recompute_normal = normal is None

        self.__zero_area = None
        self.compute_normal()

    def compute_normal(self):
        if not self.recompute_normal:
            return
        
        if any(x is None for x in [self.v1, self.v2, self.v3]):
            return
        
        normal = np.cross((self.v2-self.v1),(self.v3-self.v2))
        length = np.linalg.norm(normal)

        self.__zero_area = length == 0
        if self.__zero_area: 
            return

        self.normal = normal / length

    def compute_area(self):
        return 0.5 * np.linalg.norm(np.abs(np.cross(self.v2 - self.v1, self.v3 - self.v1)))
    
    def zero_area(self):
        return self.__zero_area if self.__zero_area is not None else self.compute_area() == 0.0
    