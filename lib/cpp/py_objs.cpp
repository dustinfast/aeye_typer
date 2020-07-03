/////////////////////////////////////////////////////////////////////////////
// Representations of the application's Python modules, for use on CPP side.
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
//
/////////////////////////////////////////////////////////////////////////////

#include <Python.h>


/////////////////////////////////////////////////////////////////////////////
// Defs

#define PY_LIB_IMPORT_STR "import sys; sys.path.insert(0, '/opt/app/src/lib/py/')"

PyObject *get_pyclass(const char *name);


/////////////////////////////////////////////////////////////////////////////
// Class EyeTrackerCoordPredict: A C representation of the python obj of the
// same name.
class EyeTrackerCoordPredict {
    public:
        long int predict(
            float eyepos_left_x, 
            float eyepos_left_y, 
            float eyepos_left_z,
            float eyepos_right_x, 
            float eyepos_right_y,
            float eyepos_right_z,
            int gaze_coord_x, 
            int gaze_coord_y
        );
        EyeTrackerCoordPredict(const char *model_path);
        ~EyeTrackerCoordPredict();

    protected:
        PyObject *m_py_self;

    private:
        PyThreadState *m_py_threadstate;
        PyGILState_STATE m_py_gilstate;
};

EyeTrackerCoordPredict::EyeTrackerCoordPredict(const char *model_path) {

    // Acquire gill lock iff needed
    if (!PyGILState_Check())
        m_py_gilstate = PyGILState_Ensure();

    Py_Initialize();
    PyEval_InitThreads();

    // Append lib dir to python path
    PyRun_SimpleString (PY_LIB_IMPORT_STR);

    // Import py module and get class attribute
    // TODO: The module is pyx, which is fine when running aeye_typer from py,
    // But import of the module will file when instantiated from c++.. Likely
    // need to do a cython setup file to fix.
    PyObject *p_module = PyImport_ImportModule("eyetracker_coord_predict");
    assert(p_module != NULL);

    PyObject *p_attr = PyObject_GetAttrString(p_module, "EyeTrackerCoordPredict");
    assert(p_attr != NULL);

    // Instantiate the class obj
    PyObject * p_obj = get_pyclass("EyeTrackerCoordPredict");
    assert(p_obj != NULL);
    
    PyObject *p_args = Py_BuildValue("(s)", model_path);
    m_py_self = PyObject_CallObject(p_attr, p_args);
    assert(m_py_self != NULL);

    // Decrement ptr refs
    Py_DECREF(p_args);
    Py_DECREF(p_obj);
    Py_DECREF(p_attr);
    Py_DECREF(p_module);
    
    // Release GIL lock
    PyGILState_Release(m_py_gilstate);
}

EyeTrackerCoordPredict::~EyeTrackerCoordPredict() {
    Py_DECREF(m_py_self);
    Py_Finalize();
}

long int EyeTrackerCoordPredict::predict(
    float eyepos_left_x, 
    float eyepos_left_y, 
    float eyepos_left_z,
    float eyepos_right_x, 
    float eyepos_right_y,
    float eyepos_right_z,
    int gaze_coord_x, 
    int gaze_coord_y
    ) {
        // Acquire gill lock iff needed
        if (!PyGILState_Check())
            m_py_gilstate = PyGILState_Ensure();

        // Call python obj's predict method
        PyObject *p_result = PyObject_CallMethod(
            m_py_self, 
            "predict", 
            "(ddddddii)",
            eyepos_left_x,
            eyepos_left_y,
            eyepos_left_z,
            eyepos_right_x,
            eyepos_right_y,
            eyepos_right_z,
            gaze_coord_x,
            gaze_coord_y
        );
        assert(p_result != NULL);

        long int pred = PyLong_AsLong(p_result);
        Py_DECREF(p_result);

        // Release GIL lock
        PyGILState_Release(m_py_gilstate);
        
        // printf("%li\n", pred);  // debug

        return pred;
}

// Helper func returning a py class (not an instance) of the given name.
PyObject* get_pyclass(const char *name)
{
    PyObject* p_name = PyUnicode_FromString(name);
    PyObject* p_base = PyTuple_New(0);
    PyObject* p_dict = PyDict_New();

    PyObject *pClass = PyObject_CallFunctionObjArgs(
        (PyObject *)&PyType_Type, p_name, p_base, p_dict, NULL);

    Py_DECREF(p_name);
    Py_DECREF(p_base);
    Py_DECREF(p_dict);

    return pClass;

}