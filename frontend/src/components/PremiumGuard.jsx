import React from 'react';
import { useAuth } from './AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Link } from 'react-router-dom';
import { Badge } from './ui/badge';

const PremiumGuard = ({ children, fallback, requiresConsultation = false }) => {
  const { user } = useAuth();
  
  // Se usuário não está logado
  if (!user) {
    return (
      <Card className="text-center p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <CardHeader>
          <div className="flex items-center justify-center mb-2">
            <Badge className="bg-blue-600 text-white">Login Necessário</Badge>
          </div>
          <CardTitle className="text-xl text-blue-700">🔐 Acesso Restrito</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-blue-600 mb-6">
            Faça login para acessar este conteúdo.
          </p>
          <div className="flex gap-4 justify-center">
            <Button asChild className="bg-blue-600 hover:bg-blue-700">
              <Link to="/login">Fazer Login</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/register">Criar Conta</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  // Se usuário não é premium
  if (!user.is_premium) {
    return fallback || (
      <Card className="text-center p-6 bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200">
        <CardHeader>
          <div className="flex items-center justify-center mb-2">
            <Badge className="bg-yellow-600 text-white">Premium</Badge>
          </div>
          <CardTitle className="text-xl text-yellow-700">⭐ Conteúdo Premium</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-yellow-600 mb-6">
            Este conteúdo está disponível apenas para assinantes Premium.
            Faça o upgrade e tenha acesso a todas as técnicas avançadas e consulta especializada!
          </p>
          <Button asChild className="bg-yellow-600 hover:bg-yellow-700">
            <Link to="/payment">Fazer Upgrade Premium</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Se requer consulta especializada mas usuário não tem
  if (requiresConsultation && !user.has_specialist_consultation) {
    return (
      <Card className="text-center p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
        <CardHeader>
          <div className="flex items-center justify-center mb-2">
            <Badge className="bg-green-600 text-white">Consulta Especializada</Badge>
          </div>
          <CardTitle className="text-xl text-green-700">🩺 Consulta Especializada Premium</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-green-600 mb-6">
            A consulta especializada via WhatsApp está incluída no seu plano Premium.
            Confirme seu pagamento para ativar este benefício!
          </p>
          <Button asChild className="bg-green-600 hover:bg-green-700">
            <Link to="/payment">Confirmar Pagamento</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }
  
  // Se tem acesso, renderiza o conteúdo
  return children;
};

export default PremiumGuard;