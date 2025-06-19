import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

interface User {
  id: string;
  email: string;
  full_name: string;
  subscription_tier: string;
  preferred_sports: string[];
  created_at: string;
  last_login: string;
  is_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
}

interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  preferred_sports?: string[];
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  // Verificar se há token salvo e validar usuário
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('auth_token');
      
      if (token) {
        try {
          const response = await apiService.getProfile();
          setUser(response.user);
        } catch (error) {
          // Token inválido ou expirado
          localStorage.removeItem('auth_token');
          console.error('Token inválido:', error);
        }
      }
      
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  // Auto-refresh token a cada 30 minutos
  useEffect(() => {
    if (isAuthenticated) {
      const interval = setInterval(async () => {
        try {
          await refreshToken();
        } catch (error) {
          console.error('Erro ao renovar token:', error);
          logout();
        }
      }, 30 * 60 * 1000); // 30 minutos

      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      
      const response = await apiService.login(email, password);
      
      // Salvar token
      localStorage.setItem('auth_token', response.access_token);
      
      // Buscar dados do usuário
      const profileResponse = await apiService.getProfile();
      setUser(profileResponse.user);
      
      toast.success(`Bem-vindo, ${profileResponse.user.full_name}!`);
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Erro ao fazer login';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    try {
      setIsLoading(true);
      
      const response = await apiService.register(data);
      
      // Salvar token
      localStorage.setItem('auth_token', response.access_token);
      
      // Buscar dados do usuário
      const profileResponse = await apiService.getProfile();
      setUser(profileResponse.user);
      
      toast.success(`Conta criada com sucesso! Bem-vindo, ${data.full_name}!`);
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Erro ao criar conta';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiService.logout();
    } catch (error) {
      // Mesmo se falhar, vamos fazer logout local
      console.error('Erro ao fazer logout:', error);
    } finally {
      localStorage.removeItem('auth_token');
      setUser(null);
      toast.success('Logout realizado com sucesso!');
    }
  };

  const refreshToken = async () => {
    try {
      const response = await apiService.refreshToken();
      localStorage.setItem('auth_token', response.access_token);
    } catch (error) {
      console.error('Erro ao renovar token:', error);
      throw error;
    }
  };

  const updateProfile = async (data: Partial<User>) => {
    try {
      // Implementar endpoint de atualização de perfil
      // const response = await apiService.updateProfile(data);
      // setUser(response.user);
      
      // Por enquanto, simulação
      setUser(prev => prev ? { ...prev, ...data } : null);
      toast.success('Perfil atualizado com sucesso!');
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Erro ao atualizar perfil';
      toast.error(errorMessage);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshToken,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Componente de proteção de rotas
interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  fallback = <LoginPage /> 
}) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white">Carregando...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// Página de Login simples
const LoginPage: React.FC = () => {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    preferred_sports: [] as string[]
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register({
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
          preferred_sports: formData.preferred_sports
        });
      }
    } catch (error) {
      // Error já foi tratado no contexto
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="card-primary p-8">
          
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto rounded-lg bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center mb-4">
              <span className="text-2xl font-bold text-gray-900">QB</span>
            </div>
            <h1 className="text-2xl font-bold text-white">QuantumBet</h1>
            <p className="text-gray-400 text-sm">A Sala de Análise</p>
          </div>

          {/* Form Toggle */}
          <div className="flex bg-gray-800 rounded-lg p-1 mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                isLogin ? 'bg-yellow-500 text-gray-900' : 'text-gray-400'
              }`}
            >
              Entrar
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                !isLogin ? 'bg-yellow-500 text-gray-900' : 'text-gray-400'
              }`}
            >
              Criar Conta
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Nome Completo
                </label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-600 text-white px-4 py-3 rounded-lg focus:border-yellow-500 focus:outline-none"
                  placeholder="Seu nome completo"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-600 text-white px-4 py-3 rounded-lg focus:border-yellow-500 focus:outline-none"
                placeholder="seu@email.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Senha
              </label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-600 text-white px-4 py-3 rounded-lg focus:border-yellow-500 focus:outline-none"
                placeholder="Sua senha"
              />
            </div>

            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Esportes de Interesse
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {['Futebol', 'Basquete', 'Tênis', 'Americano'].map((sport) => (
                    <label key={sport} className="flex items-center">
                      <input
                        type="checkbox"
                        value={sport.toLowerCase()}
                        onChange={(e) => {
                          const value = e.target.value;
                          setFormData(prev => ({
                            ...prev,
                            preferred_sports: e.target.checked
                              ? [...prev.preferred_sports, value]
                              : prev.preferred_sports.filter(s => s !== value)
                          }));
                        }}
                        className="mr-2 rounded text-yellow-500 focus:ring-yellow-500"
                      />
                      <span className="text-gray-300 text-sm">{sport}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-value py-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Carregando...' : (isLogin ? 'Entrar' : 'Criar Conta')}
            </button>
          </form>

          {/* Demo Access */}
          <div className="mt-6 pt-6 border-t border-gray-700 text-center">
            <p className="text-gray-400 text-sm mb-2">Acesso de demonstração:</p>
            <button
              onClick={() => {
                setFormData({ email: 'demo@quantumbet.com', password: 'demo123', full_name: '', preferred_sports: [] });
                setIsLogin(true);
              }}
              className="text-yellow-400 text-sm hover:underline"
            >
              Usar conta demo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}; 