import { useNavigate } from "react-router-dom"
import { useMutation, useQuery} from '@tanstack/react-query';
import axios from "axios";
import { jwtDecode } from "jwt-decode";
import toast from "react-hot-toast";

const BaseURL = 'http://127.0.0.1:8000/'

export const useRegister = () => {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (data) => {
      const response = await axios.post(
        `${BaseURL}/api/register/`,
        data,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;

    },
    onSuccess: (data) => {
      toast.success('Registration successful');
      navigate('/login');
    },
  });
};

export const useLogin = () => {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (credentials) => {
      const response = await axios.post(
        `${BaseURL}/api/token/`,
        credentials,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('accessToken', data.access);
      localStorage.setItem('refreshToken', data.refresh);
      const decodedUser = jwtDecode(data.access)
      localStorage.setItem('user', JSON.stringify(decodedUser))
      toast.success('Logged in Succesfully');
      navigate('/joblist');
    },
  });
};



export const useLogout = () => {
  const navigate = useNavigate();

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    toast.success('Logged out successfully!');
    navigate('/');
  };

  return logout;
};


export const useJobForm = () => {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (data) => {
      const response = await axios.post(
        `${BaseURL}/api/job/`,
        data,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      return response.data;

    },
    onSuccess: (data) => {
      toast.success('Job Position Created');
      navigate('/joblist');
    },
    onError: (error) => {
      toast.error(error)

    }
  });
};
export const useJobApplication = () => {
  return useMutation({
    mutationFn: async (id) => {
      const response = await axios.post(
        `${BaseURL}/api/apply/${id}/`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      return response.data;
    },
  });
};

export const useViewAllJobs = () => {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      const response = await axios.get(`${BaseURL}/api/job/`);
      return response?.data
    },
  });
};



export const JobApplicationView = (jobId) => {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: async () => {
      const response = await axios.get(`${BaseURL}/api/job_application/${jobId}`);
      return response.data;

    },
  });
};

export const useEditApplication = () => {

  return useMutation({
    mutationFn: async (params) => {
      const { id, data } = params;
      const response = await axios.put(
        `${BaseURL}/api/job_application/${id}`,
        data,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      return response.data;

    },
    onSuccess: (data) => {
      toast.success('Application Updated Successfully')
      console.log(data);
    },
  });
};

export const useSendEmail = () => {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (id) => {
      const response = await axios.post(
        `${BaseURL}/api/send_application/${id}`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('Email Send Succesfully')
      navigate('/joblist')
    },
  });
};

export const UserProfileView = () => {
  return useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const response = await axios.get(`${BaseURL}/api/profile/`);
      return response.data;
    },
  });
};

export const UserAppliedJobs = () => {
  return useQuery({
    queryKey: ['Appled jobs'],
    queryFn: async () => {
      const response = await axios.get(`${BaseURL}/api/user-applied-jobs/`);
      return response.data;
    },
  });
};

