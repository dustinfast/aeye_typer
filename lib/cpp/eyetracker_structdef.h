/////////////////////////////////////////////////////////////////////////////
// Misc structs for use by the eyetracker modules.
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
//
/////////////////////////////////////////////////////////////////////////////

typedef struct gaze_data {
        int64_t unixtime_us;

        float left_pupildiameter_mm;
        float right_pupildiameter_mm;

        float left_eyeposition_normed_x;
		float left_eyeposition_normed_y;
		float left_eyeposition_normed_z;
		float right_eyeposition_normed_x;
		float right_eyeposition_normed_y;
		float right_eyeposition_normed_z;

        float left_eyecenter_mm_x;
		float left_eyecenter_mm_y;
		float left_eyecenter_mm_z;
		float right_eyecenter_mm_x;
		float right_eyecenter_mm_y;
		float right_eyecenter_mm_z;

        float left_gazeorigin_mm_x;
		float left_gazeorigin_mm_y;
		float left_gazeorigin_mm_z;
		float right_gazeorigin_mm_x;
		float right_gazeorigin_mm_y;
		float right_gazeorigin_mm_z;

        float left_gazepoint_mm_x;
		float left_gazepoint_mm_y;
		float left_gazepoint_mm_z;
		float right_gazepoint_mm_x;
		float right_gazepoint_mm_y;
		float right_gazepoint_mm_z;

        float left_gazepoint_normed_x;
		float left_gazepoint_normed_y;
		float right_gazepoint_normed_x;
		float right_gazepoint_normed_y;

        int combined_gazepoint_x;
        int combined_gazepoint_y;
	    } gaze_data_t;

typedef struct gaze_point {
        int n_samples;
        int x_coord;
        int y_coord;
	    } gaze_point_t;
