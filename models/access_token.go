package models

import (
	"github.com/Viva-con-Agua/vcago"
	"github.com/Viva-con-Agua/vcago/vmdb"
	"github.com/Viva-con-Agua/vcago/vmod"
	"github.com/golang-jwt/jwt"
	"go.mongodb.org/mongo-driver/bson"
)

type AccessToken struct {
	ID             string              `json:"id,omitempty" bson:"_id"`
	Email          string              `json:"email" bson:"email" validate:"required,email"`
	FirstName      string              `bson:"first_name" json:"first_name" validate:"required"`
	LastName       string              `bson:"last_name" json:"last_name" validate:"required"`
	FullName       string              `bson:"full_name" json:"full_name"`
	DisplayName    string              `bson:"display_name" json:"display_name"`
	Roles          vmod.RoleListCookie `json:"system_roles" bson:"system_roles"`
	Country        string              `bson:"country" json:"country"`
	PrivacyPolicy  bool                `bson:"privacy_policy" json:"privacy_policy"`
	Confirmd       bool                `bson:"confirmed" json:"confirmed"`
	LastUpdate     string              `bson:"last_update" json:"last_update"`
	Phone          string              `json:"phone"`
	Gender         string              `json:"gender"`
	Birthdate      int64               `json:"birthdate"`
	CrewName       string              `json:"crew_name"`
	CrewID         string              `json:"crew_id"`
	OrganisationID string              `json:"organisation_id"`
	CrewEmail      string              `json:"crew_email"`
	AddressID      string              `json:"address_id"`
	PoolRoles      vmod.RoleListCookie `json:"pool_roles"`
	ActiveState    string              `json:"active_state"`
	NVMState       string              `json:"nvm_state"`
	AvatarID       string              `json:"avatar_id"`
	MailboxID      string              `json:"mailbox_id"`
	Modified       vmod.Modified       `json:"modified"`
	jwt.StandardClaims
}

func (token *AccessToken) AccessPermission() (err error) {
	if !token.Roles.Validate("admin") {
		return vcago.NewPermissionDenied(OrganisationCollection)
	}
	return
}

func (token *AccessToken) AddressCreate(id string) (err error) {
	if !token.Roles.Validate("admin") && token.ID != id {
		return vcago.NewPermissionDenied(AddressesCollection)
	}
	return
}

// CrewFilter restricts the filter to documents of the crew of the token user.
// vmdb.Filter.EqualString drops empty values, so for a user without crew the restriction would
// silently disappear and match all documents. In that case the filter matches nothing instead.
func CrewFilter(filter *vmdb.Filter, key string, token *AccessToken) {
	if token.CrewID == "" {
		filter.Append(bson.E{Key: key, Value: bson.D{{Key: "$in", Value: bson.A{}}}})
		return
	}
	filter.EqualString(key, token.CrewID)
}
